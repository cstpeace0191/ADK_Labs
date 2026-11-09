"""`adk create my_agent` 골격을 슬라이드 45 '첫 번째 에이전트'로 채운 버전.

part03_cli 폴더에서:
    adk run my_agent
    adk web --port 8000
"""
import os

from google.adk import Agent


def get_weather(city: str) -> dict:
    """지정한 도시의 현재 날씨를 반환한다."""
    data = {"서울": "맑음, 18°C", "부산": "흐림, 20°C"}
    if city in data:
        return {"status": "success", "report": data[city]}
    return {"status": "error", "error_message": f"{city} 정보 없음"}


root_agent = Agent(
    name="weather_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    description="도시 날씨를 알려주는 에이전트",
    instruction="사용자가 묻는 도시의 날씨를 get_weather로 조회해 한 문장으로 답하라.",
    tools=[get_weather],
)
