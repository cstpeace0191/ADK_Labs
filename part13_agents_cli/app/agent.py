"""agents-cli 가 생성하는 app/agent.py 의 구조를 그대로 따른 날씨·시각 에이전트.

agents-cli create (base_template=adk_python) 결과물의 핵심 3가지:
  1) 도구는 평범한 파이썬 함수 (docstring = 모델이 읽는 도구 설명)
  2) model=Gemini(..., retry_options=...) 로 429/5xx 재시도를 모델 객체에 내장
  3) root_agent 를 App(name="app") 으로 감싼다 → 서버·Agent Runtime·eval 이 모두 이 App 을 쓴다

원본: agents-cli-workflow/app/agent.py (Open-Meteo 실시간 API).
실습용 보완: 네트워크가 없으면 _OFFLINE 표의 값으로 대답한다(단위 테스트가 오프라인에서도 통과).
"""
from __future__ import annotations

import datetime
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

# .env 는 MODEL 을 읽기 전에 로드해야 한다 (app/__init__.py 가 이 모듈을 가장 먼저 import 한다).
# 프로젝트 .env → 실습 루트(ADK_Labs/.env) 순서, 이미 설정된 환경변수는 덮어쓰지 않는다.
_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT.parent / ".env")

from google.adk.agents import Agent  # noqa: E402
from google.adk.apps import App  # noqa: E402
from google.adk.models import Gemini  # noqa: E402
from google.genai import types  # noqa: E402

# 원본은 "gemini-3.8-flash" 고정. 실습에서는 .env 의 ADK_MODEL 로 바꿀 수 있게 했다.
MODEL = os.getenv("ADK_MODEL", "gemini-3.8-flash")
OFFLINE = os.getenv("AGENT_OFFLINE", "0") == "1"  # 1 이면 외부 API를 호출하지 않는다

WMO_WEATHER_CODES = {
    0: "맑음", 1: "대체로 맑음", 2: "구름 조금", 3: "흐림", 45: "안개", 48: "서리 안개",
    51: "약한 이슬비", 53: "이슬비", 55: "강한 이슬비", 61: "약한 비", 63: "비", 65: "강한 비",
    71: "약한 눈", 73: "눈", 75: "강한 눈", 80: "약한 소나기", 81: "소나기", 82: "강한 소나기",
    95: "뇌우", 96: "우박 동반 뇌우", 99: "강한 우박 동반 뇌우",
}

# 오프라인 대체값: (표시 이름, 위도, 경도, 시간대)
_OFFLINE = {
    "seoul": ("Seoul, South Korea", 37.5665, 126.9780, "Asia/Seoul"),
    "서울": ("서울, 대한민국", 37.5665, 126.9780, "Asia/Seoul"),
    "tokyo": ("Tokyo, Japan", 35.6762, 139.6503, "Asia/Tokyo"),
    "도쿄": ("도쿄, 일본", 35.6762, 139.6503, "Asia/Tokyo"),
    "san francisco": ("San Francisco, United States", 37.7749, -122.4194, "America/Los_Angeles"),
    "paris": ("Paris, France", 48.8566, 2.3522, "Europe/Paris"),
}
_HEADERS = {"User-Agent": "ADK-Labs/1.0 (lecture example)"}


def _get_json(url: str, timeout: int = 5) -> dict:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def geocode(location: str) -> dict:
    """도시·지역 이름을 위도와 경도로 바꾼다.

    Args:
        location: 도시나 지역 이름 (예: 'Seoul', '서울', 'Paris').

    Returns:
        status, location, display_name, latitude, longitude 를 담은 dict.
    """
    key = location.strip().lower()
    if not OFFLINE:
        try:  # Open-Meteo Geocoding API (키 불필요)
            url = ("https://geocoding-api.open-meteo.com/v1/search?count=1&format=json&name="
                   + urllib.parse.quote(location))
            results = _get_json(url).get("results") or []
            if results:
                it = results[0]
                name = ", ".join(x for x in (it.get("name"), it.get("country")) if x)
                return {"status": "success", "location": location, "display_name": name,
                        "latitude": float(it["latitude"]), "longitude": float(it["longitude"]),
                        "timezone": it.get("timezone", "UTC")}
        except Exception:
            pass  # 네트워크 실패 → 오프라인 표로 대체
    if key in _OFFLINE:
        name, lat, lng, tz = _OFFLINE[key]
        return {"status": "success", "location": location, "display_name": name,
                "latitude": lat, "longitude": lng, "timezone": tz, "source": "offline"}
    return {"status": "error", "message": f"좌표를 찾을 수 없습니다: {location}"}


def _resolve(location: str, latitude: float | None, longitude: float | None):
    """이름 또는 좌표를 (표시 이름, 위도, 경도, 시간대) 로 정리한다."""
    if latitude is not None and longitude is not None:
        return location or f"({latitude:.4f}, {longitude:.4f})", latitude, longitude, None
    if not location:
        return None
    geo = geocode(location)
    if geo.get("status") != "success":
        return None
    return geo["display_name"], geo["latitude"], geo["longitude"], geo.get("timezone")


def get_weather(location: str = "", latitude: float | None = None,
                longitude: float | None = None) -> str:
    """도시 이름 또는 위도·경도로 현재 날씨를 조회한다.

    Args:
        location: 도시나 지역 이름. 좌표를 주면 생략할 수 있다.
        latitude: 위도 (선택).
        longitude: 경도 (선택).

    Returns:
        날씨 상태, 기온, 체감온도, 습도, 풍속을 담은 문자열.
    """
    r = _resolve(location, latitude, longitude)
    if r is None:
        return "도시 이름이나 위도·경도를 알려주세요."
    name, lat, lng, _ = r
    if not OFFLINE:
        try:
            url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}"
                   "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
                   "weather_code,wind_speed_10m&timezone=auto")
            cur = _get_json(url).get("current", {})
            cond = WMO_WEATHER_CODES.get(cur.get("weather_code", 0), "알 수 없음")
            return (f"Weather for {name} ({lat:.4f}, {lng:.4f}):\n"
                    f"- Condition: {cond}\n"
                    f"- Temperature: {cur.get('temperature_2m')}°C "
                    f"(Feels like: {cur.get('apparent_temperature')}°C)\n"
                    f"- Relative Humidity: {cur.get('relative_humidity_2m')}%\n"
                    f"- Wind Speed: {cur.get('wind_speed_10m')} km/h")
        except Exception:
            pass
    return (f"Weather for {name} ({lat:.4f}, {lng:.4f}) [offline sample]:\n"
            "- Condition: 맑음\n- Temperature: 18°C (Feels like: 17°C)\n"
            "- Relative Humidity: 45%\n- Wind Speed: 7 km/h")


def get_current_time(location: str = "", latitude: float | None = None,
                     longitude: float | None = None) -> str:
    """도시 이름 또는 위도·경도로 현지 시각을 조회한다.

    Args:
        location: 도시나 지역 이름. 좌표를 주면 생략할 수 있다.
        latitude: 위도 (선택).
        longitude: 경도 (선택).

    Returns:
        현지 시각과 시간대를 담은 문자열.
    """
    r = _resolve(location, latitude, longitude)
    if r is None:
        return "도시 이름이나 위도·경도를 알려주세요."
    name, lat, lng, tz_name = r
    if tz_name is None and not OFFLINE:
        try:  # 좌표만 받은 경우 Open-Meteo 로 시간대를 알아낸다
            tz_name = _get_json(f"https://api.open-meteo.com/v1/forecast?latitude={lat}"
                                f"&longitude={lng}&current=temperature_2m&timezone=auto")["timezone"]
        except Exception:
            tz_name = None
    tz_name = tz_name or "Asia/Seoul"
    now = datetime.datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
    return (f"The current local time for '{name}' at ({lat:.4f}, {lng:.4f}) "
            f"in timezone '{tz_name}' is {now}.")


INSTRUCTION = """너는 정확하고 친절한 범용 비서다.

1. 날씨·현지 시각 질문: 도시 이름을 그대로 get_weather / get_current_time 에 넘긴다
   (필요하면 geocode 로 좌표를 먼저 구한다). 도시 이름, 시각, 기온, 날씨를 자연스럽게 정리해 답한다.
2. 그 밖의 질문(인사, 일반 지식): 도구를 부르지 말고 바로 답한다.
"""

root_agent = Agent(
    # agents-cli-manifest.yaml 의 create_params.root_agent_name 과 같아야 한다
    # (텔레메트리의 gen_ai.agent.name, agents-cli 가 보고하는 이름).
    name="agents_cli_workflow",
    description="도시의 현재 날씨와 현지 시각을 알려주고 일반 질문에도 답하는 비서",  # Agent Card 설명
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3)),
    instruction=INSTRUCTION,
    tools=[geocode, get_weather, get_current_time],
)

# App: 에이전트 + 이름(= 서버의 /apps/{app_name}) + 플러그인 등 앱 단위 설정을 묶는다.
app = App(root_agent=root_agent, name="app")
