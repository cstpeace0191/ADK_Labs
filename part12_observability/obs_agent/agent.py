"""강의노트 Part 12 슬라이드 137: adk web Trace 탭 · --otel_to_cloud · OTLP 확인용 에이전트. 🔑 Gemini 키 필요.

part12_observability 폴더에서:
  adk web --port 8000                              # Trace 탭에서 span 트리 보기
  OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 adk web --port 8000   # Jaeger 등 OTLP 백엔드로도 보내기
  adk web --otel_to_cloud --port 8000              # Cloud Trace · Cloud Logging (GCP 프로젝트 · 인증 필요)
"""
import os

from google.adk import Agent


def get_weather(city: str) -> dict:
    """도시의 현재 날씨를 돌려준다. 실습용 고정 값이며 모르는 도시는 오류를 돌려준다."""
    table = {"Seoul": ("맑음", 21), "Busan": ("흐림", 19), "서울": ("맑음", 21), "부산": ("흐림", 19)}
    if city not in table:
        return {"status": "error", "message": f"{city} 날씨 정보 없음"}
    sky, temp = table[city]
    return {"status": "ok", "city": city, "sky": sky, "temp_c": temp}


def get_time(city: str) -> dict:
    """도시의 현재 시각(Asia/Seoul 기준 실습용)을 돌려준다."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return {"city": city, "time": datetime.now(ZoneInfo("Asia/Seoul")).strftime("%H:%M")}


root_agent = Agent(
    name="obs_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    instruction="날씨는 get_weather, 시각은 get_time 도구로 확인해 한두 문장으로 답한다. 도구가 오류면 솔직히 말한다.",
    tools=[get_weather, get_time],
)
