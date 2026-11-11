# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""전세계 도시의 실제 현재 시각과 날씨를 실시간으로 제공하고 일반 질문에도 친절하게 답변하는 AI 어시스턴트."""
from __future__ import annotations

import datetime
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

# .env 환경 변수 로드
_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env", override=True)
load_dotenv(_ROOT.parent.parent / ".env")

if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() in ("TRUE", "1"):
    os.environ.pop("GOOGLE_API_KEY", None)
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")

MODEL = os.getenv("ADK_MODEL", "gemini-3.8-flash")
OFFLINE = os.getenv("AGENT_OFFLINE", "0") == "1"
_HEADERS = {"User-Agent": "ADK-Labs/1.0 (my-agents-cli-mod)"}

# WMO 기상 코드 한국어 매핑
WMO_WEATHER_CODES = {
    0: "맑음",
    1: "대체로 맑음",
    2: "구름 조금",
    3: "흐림",
    45: "안개",
    48: "서리 안개",
    51: "약한 이슬비",
    53: "이슬비",
    55: "강한 이슬비",
    61: "약한 비",
    63: "비",
    65: "강한 비",
    71: "약한 눈",
    73: "눈",
    75: "강한 눈",
    80: "약한 소나기",
    81: "소나기",
    82: "강한 소나기",
    95: "뇌우",
    96: "우박 동반 뇌우",
    99: "강한 우박 동반 뇌우",
}

# 주요 한국어 도시명 영문 변환 사전 (Open-Meteo Geocoding API 검색 호환성)
KOREAN_CITY_MAP = {
    "서울": "Seoul",
    "부산": "Busan",
    "제주": "Jeju",
    "인천": "Incheon",
    "대구": "Daegu",
    "대전": "Daejeon",
    "광주": "Gwangju",
    "울산": "Ulsan",
    "수원": "Suwon",
    "도쿄": "Tokyo",
    "오사카": "Osaka",
    "베이징": "Beijing",
    "상하이": "Shanghai",
    "런던": "London",
    "파리": "Paris",
    "로마": "Rome",
    "베를린": "Berlin",
    "마드리드": "Madrid",
    "뉴욕": "New York",
    "로스앤젤레스": "Los Angeles",
    "샌프란시스코": "San Francisco",
    "시카고": "Chicago",
    "시애틀": "Seattle",
    "시드니": "Sydney",
    "토론토": "Toronto",
    "싱가포르": "Singapore",
    "방콕": "Bangkok",
    "두바이": "Dubai",
}

# 네트워크 단절 또는 오프라인 환경을 위한 기본 백업 데이터
_OFFLINE = {
    "seoul": ("Seoul, South Korea", 37.5665, 126.9780, "Asia/Seoul"),
    "서울": ("서울, 대한민국", 37.5665, 126.9780, "Asia/Seoul"),
    "busan": ("Busan, South Korea", 35.1796, 129.0756, "Asia/Seoul"),
    "부산": ("부산, 대한민국", 35.1796, 129.0756, "Asia/Seoul"),
    "jeju": ("Jeju, South Korea", 33.4996, 126.5312, "Asia/Seoul"),
    "제주": ("제주, 대한민국", 33.4996, 126.5312, "Asia/Seoul"),
    "tokyo": ("Tokyo, Japan", 35.6762, 139.6503, "Asia/Tokyo"),
    "도쿄": ("도쿄, 일본", 35.6762, 139.6503, "Asia/Tokyo"),
    "new york": ("New York, United States", 40.7128, -74.0060, "America/New_York"),
    "뉴욕": ("뉴욕, 미국", 40.7128, -74.0060, "America/New_York"),
    "paris": ("Paris, France", 48.8566, 2.3522, "Europe/Paris"),
    "파리": ("파리, 프랑스", 48.8566, 2.3522, "Europe/Paris"),
    "london": ("London, United Kingdom", 51.5074, -0.1278, "Europe/London"),
    "런던": ("런던, 영국", 51.5074, -0.1278, "Europe/London"),
    "san francisco": ("San Francisco, United States", 37.7749, -122.4194, "America/Los_Angeles"),
    "sf": ("San Francisco, United States", 37.7749, -122.4194, "America/Los_Angeles"),
    "샌프란시스코": ("샌프란시스코, 미국", 37.7749, -122.4194, "America/Los_Angeles"),
    "sydney": ("Sydney, Australia", -33.8688, 151.2093, "Australia/Sydney"),
    "시드니": ("시드니, 호주", -33.8688, 151.2093, "Australia/Sydney"),
}


def _get_json(url: str, timeout: int = 5) -> dict:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def geocode(location: str) -> dict:
    """전세계 도시 또는 지역 이름을 검색하여 위도, 경도, 표준 시간대(Timezone) 정보를 반환한다.

    Args:
        location: 검색할 도시 또는 지역 이름 (예: 'Seoul', '서울', 'Tokyo', '도쿄', 'New York', 'Paris', '런던', 'San Francisco').

    Returns:
        status, location, display_name, latitude, longitude, timezone 을 포함하는 dict.
    """
    cleaned = location.strip()
    key = cleaned.lower()
    search_query = KOREAN_CITY_MAP.get(cleaned, cleaned)

    if not OFFLINE:
        try:
            url = (
                "https://geocoding-api.open-meteo.com/v1/search?count=1&format=json&name="
                + urllib.parse.quote(search_query)
            )
            data = _get_json(url)
            results = data.get("results") or []
            if results:
                item = results[0]
                country = item.get("country", "")
                name = item.get("name", location)
                display_name = f"{name}, {country}" if country else name
                return {
                    "status": "success",
                    "location": location,
                    "display_name": display_name,
                    "latitude": float(item["latitude"]),
                    "longitude": float(item["longitude"]),
                    "timezone": item.get("timezone", "UTC"),
                }
        except Exception:
            pass

    # 네트워크 요청 실패 또는 오프라인 모드 시 대체 데이터 활용
    if key in _OFFLINE:
        name, lat, lng, tz = _OFFLINE[key]
        return {
            "status": "success",
            "location": location,
            "display_name": name,
            "latitude": lat,
            "longitude": lng,
            "timezone": tz,
            "source": "offline",
        }

    return {"status": "error", "message": f"좌표 및 시간대를 찾을 수 없습니다: '{location}'"}


def _resolve(location: str, latitude: float | None, longitude: float | None):
    """도시 이름 또는 좌표로부터 (표시 이름, 위도, 경도, 시간대)를 파악한다."""
    if latitude is not None and longitude is not None:
        return location or f"({latitude:.4f}, {longitude:.4f})", latitude, longitude, None
    if not location:
        return None
    geo = geocode(location)
    if geo.get("status") != "success":
        return None
    return geo["display_name"], geo["latitude"], geo["longitude"], geo.get("timezone")


def get_current_time(
    location: str = "",
    query: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """도시 이름 또는 좌표를 바탕으로 해당 지역의 실제 현재 시각(Local Time)을 조회한다.

    Args:
        location: 도시나 지역 이름 (예: '서울', 'Seoul', 'Tokyo', 'New York', 'Paris', 'San Francisco').
        query: location의 대체 매개변수.
        latitude: 위도 (선택).
        longitude: 경도 (선택).

    Returns:
        status, location, timezone, current_time, message 를 담은 dict.
    """
    target = location.strip() or query.strip()
    res = _resolve(target, latitude, longitude)
    if res is None:
        return {"status": "error", "message": f"시각을 확인할 도시 이름이나 좌표를 찾을 수 없습니다: '{target}'"}

    name, lat, lng, tz_name = res
    if tz_name is None and not OFFLINE:
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}"
                "&current=temperature_2m&timezone=auto"
            )
            tz_name = _get_json(url).get("timezone")
        except Exception:
            tz_name = None

    tz_name = tz_name or "Asia/Seoul"
    try:
        now = datetime.datetime.now(ZoneInfo(tz_name))
    except Exception:
        now = datetime.datetime.now(datetime.timezone.utc)
        tz_name = "UTC"

    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
    return {
        "status": "success",
        "location": name,
        "latitude": lat,
        "longitude": lng,
        "timezone": tz_name,
        "current_time": formatted_time,
        "message": f"현재 '{name}' (위도 {lat:.4f}, 경도 {lng:.4f}, 시간대 {tz_name})의 현지 시각은 {formatted_time} 입니다.",
    }


def get_weather(
    location: str = "",
    query: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """도시 이름 또는 좌표를 바탕으로 해당 지역의 실제 현재 날씨와 기온 정보를 실시간 조회한다.

    Args:
        location: 도시나 지역 이름 (예: '서울', 'Seoul', 'Paris', 'Tokyo', 'New York', '샌프란시스코').
        query: location의 대체 매개변수.
        latitude: 위도 (선택).
        longitude: 경도 (선택).

    Returns:
        status, location, condition, temperature, feels_like, humidity, wind_speed, message 를 담은 dict.
    """
    target = location.strip() or query.strip()
    res = _resolve(target, latitude, longitude)
    if res is None:
        return {"status": "error", "message": f"날씨를 확인할 도시 이름이나 좌표를 찾을 수 없습니다: '{target}'"}

    name, lat, lng, _ = res
    if not OFFLINE:
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}"
                "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
                "weather_code,wind_speed_10m&timezone=auto"
            )
            cur = _get_json(url).get("current", {})
            code = cur.get("weather_code", 0)
            condition = WMO_WEATHER_CODES.get(code, "알 수 없음")
            temp = cur.get("temperature_2m")
            feels_like = cur.get("apparent_temperature")
            humidity = cur.get("relative_humidity_2m")
            wind_speed = cur.get("wind_speed_10m")

            return {
                "status": "success",
                "location": name,
                "latitude": lat,
                "longitude": lng,
                "condition": condition,
                "temperature": temp,
                "apparent_temperature": feels_like,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "message": (
                    f"'{name}'의 현재 날씨:\n"
                    f"- 날씨 상태: {condition}\n"
                    f"- 기온: {temp}°C (체감 온도: {feels_like}°C)\n"
                    f"- 습도: {humidity}%\n"
                    f"- 풍속: {wind_speed} km/h"
                ),
            }
        except Exception:
            pass

    # 네트워크 요청 실패 시 기본 오프라인 응답
    return {
        "status": "success",
        "location": name,
        "latitude": lat,
        "longitude": lng,
        "condition": "맑음",
        "temperature": 18.0,
        "apparent_temperature": 17.0,
        "humidity": 45,
        "wind_speed": 7.0,
        "source": "offline_fallback",
        "message": f"'{name}'의 현재 날씨(오프라인 기준): 맑음, 기온 18.0°C, 습도 45%",
    }


INSTRUCTION = """너는 친절하고 유능하며 정확한 범용 AI 어시스턴트다.

[핵심 행동 수칙]
1. 전세계 도시의 현지 시각 및 날씨 질문:
   - 사용자가 특정 도시나 지역의 현재 시간, 날씨, 기온, 기상 상태 등을 물어보면 제공된 도구(`geocode`, `get_current_time`, `get_weather`)를 적극 활용합니다.
   - 필요에 따라 `geocode` 도구로 위도·경도 및 표준 시간대를 먼저 파악하거나, `get_current_time` 및 `get_weather` 도구에 도시 이름을 직접 전달합니다.
   - 도구 실행 결과로 얻은 실제 현지 시각, 기온, 체감 온도, 날씨 상태(맑음, 흐림, 비 등), 습도, 풍속 등을 종합하여 사용자에게 자연스럽고 친절한 한국어로 답변합니다.

2. 시간 및 날씨 이외의 모든 질문 (일반 질문):
   - 외부 도구 호출이 필요 없는 모든 질문(인사, 일상 대화, 상식, 과학, 역사, 인문학, 프로그래밍, 글쓰기, 번역, 요약, 조언 등)에는 도구를 절대 호출하지 않습니다.
   - 네 풍부한 지식을 바탕으로 가능한 한 모든 질문에 성실하고 상세하며 최대한 친절하게 답변합니다.
"""

root_agent = Agent(
    # Keep in sync with create_params.root_agent_name in agents-cli-manifest.yaml:
    name="my_agents_cli_mod",
    description="전세계 도시의 실제 현재 시각과 날씨를 실시간으로 조회하고 일반 질문에도 친절히 답변하는 범용 비서",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    tools=[geocode, get_current_time, get_weather],
)

app = App(
    root_agent=root_agent,
    name="app",
)
