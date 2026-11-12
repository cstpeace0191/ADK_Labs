"""`adk create my_agent_mod` 골격을 슬라이드 50 '첫 번째 에이전트'로 채운 버전.

part03_cli 폴더에서:
    adk run my_agent_mod
    adk web --port 8000
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk import Agent

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)
if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() in ("TRUE", "1"):
    os.environ.pop("GOOGLE_API_KEY", None)
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
else:
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
    os.environ.pop("GOOGLE_CLOUD_LOCATION", None)


def get_weather(city: str) -> dict:
    """지정한 도시의 현재 날씨를 반환한다."""
    data = {"서울": "맑음, 18°C", "부산": "흐림, 20°C"}
    if city in data:
        return {"status": "success", "report": data[city]}
    return {"status": "error", "error_message": f"{city} 정보 없음"}


root_agent = Agent(
    name="weather_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    description="일반 질문 답변 및 도시 날씨를 알려주는 에이전트",
    instruction="사용자가 묻는 도시의 날씨를 get_weather로 조회해 한 문장으로 답하고, 그밖의 질문은 아느대로 답해줘.",
    tools=[get_weather],
)
