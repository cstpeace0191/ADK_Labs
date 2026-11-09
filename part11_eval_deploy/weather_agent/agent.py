"""part11 평가·배포 대상 에이전트 (Part 4 슬라이드 45 날씨 에이전트)."""
import os

from google.adk import Agent


def get_weather(city: str) -> dict:
    """지정한 도시의 현재 날씨를 반환한다.

    Args:
        city: 도시 이름 (예: "서울")
    """
    data = {"서울": "맑음, 18°C", "부산": "흐림, 20°C"}
    if city in data:
        return {"status": "success", "report": data[city]}
    return {"status": "error", "error_message": f"{city} 정보 없음"}


root_agent = Agent(
    name="weather_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    description="도시 날씨를 알려주는 에이전트",
    instruction="사용자가 묻는 도시의 날씨를 get_weather로 조회해 한 문장으로 답하라. "
                "도시 이름은 '서울', '부산'처럼 한글로 넘긴다.",
    tools=[get_weather],
)
