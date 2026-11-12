"""Version of the `adk create my_agent_mod` scaffold completed as the "First Agent" example from slide 50.

Run from the part03_cli folder:
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
    """Return the current weather for the specified city."""
    data = {"Seoul": "Clear, 18°C", "Busan": "Cloudy, 20°C"}
    if city in data:
        return {"status": "success", "report": data[city]}
    return {"status": "error", "error_message": f"No data available for {city}"}


root_agent = Agent(
    name="weather_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    description="An agent that answers general questions and provides city weather.",
    instruction="Use get_weather to look up the weather for a city the user asks about and answer in one sentence. Answer other questions using your general knowledge.",
    tools=[get_weather],
)
