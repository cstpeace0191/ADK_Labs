import os
import sys
import uuid
import warnings
from typing import Optional
from zoneinfo import ZoneInfo
import datetime
import requests
from dotenv import load_dotenv

# Ensure UTF-8 output (prevents encoding issues on Windows console)
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load .env environment variables (override existing environment variables)
load_dotenv(override=True)

# Prevent duplicate warning between GOOGLE_API_KEY and GEMINI_API_KEY
os.environ.pop("GOOGLE_API_KEY", None)

# Suppress unnecessary warnings regarding ADK experimental features
warnings.filterwarnings("ignore", category=UserWarning)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

APP_NAME = "weather_time_fastapi_app"
DEFAULT_USER_ID = "user01"


# ─────────────────────────────────────────────
# City name -> Latitude/Longitude/Timezone lookup (Open-Meteo Geocoding)
# ─────────────────────────────────────────────
def _geocode(city: str):
    """Converts a city name to latitude, longitude, and timezone."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    resp = requests.get(url, params={"name": city, "count": 1, "language": "en"}, timeout=5)
    results = resp.json().get("results")
    if not results:
        return None
    r = results[0]
    return r["latitude"], r["longitude"], r["timezone"]


# ─────────────────────────────────────────────
# Tool 1: Global weather lookup (Open-Meteo Weather API)
# ─────────────────────────────────────────────
def get_weather(city: str) -> dict:
    """Retrieves the current weather report for any city in the world.

    Args:
        city (str): The name of the city (e.g. Seoul, Paris, New York).

    Returns:
        dict: status and result or error msg.
    """
    geo = _geocode(city)
    if geo is None:
        return {"status": "error", "error_message": f"City '{city}' not found."}

    lat, lon, _ = geo
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "wind_speed_unit": "ms",
    }
    data = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=5).json()
    cur = data.get("current", {})

    wmo_desc = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Icy fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
    }
    code = cur.get("weather_code", -1)
    condition = wmo_desc.get(code, f"Weather code {code}")
    report = (
        f"Weather in {city}: {condition}. "
        f"Temperature: {cur.get('temperature_2m', 'N/A')}°C, "
        f"Humidity: {cur.get('relative_humidity_2m', 'N/A')}%, "
        f"Wind: {cur.get('wind_speed_10m', 'N/A')} m/s."
    )
    return {"status": "success", "report": report}


# ─────────────────────────────────────────────
# Tool 2: Global current time lookup (Geocoding API timezone)
# ─────────────────────────────────────────────
def get_current_time(city: str) -> dict:
    """Returns the current local time for any city in the world.

    Args:
        city (str): The name of the city (e.g. Tokyo, London, Sydney).

    Returns:
        dict: status and result or error msg.
    """
    geo = _geocode(city)
    if geo is None:
        return {"status": "error", "error_message": f"City '{city}' not found."}

    _, _, tz_name = geo
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        return {"status": "error", "error_message": f"Unknown timezone '{tz_name}' for {city}."}

    now = datetime.datetime.now(tz)
    report = f"The current time in {city} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}."
    return {"status": "success", "report": report}


# ─────────────────────────────────────────────
# Agent & ADK Runner Configuration
# ─────────────────────────────────────────────
agent = LlmAgent(
    model="gemini-3.5-flash",
    name="weather_and_time_agent",
    instruction=(
        "You are a versatile, helpful AI assistant. "
        "When the user asks about the current weather or local time for a specific city, "
        "always use the provided tools (get_weather, get_current_time) to retrieve accurate, real-time information. "
        "For general knowledge questions, explanations, discussions, or any other topics, "
        "answer directly using your broad general intelligence. "
        "Always respond politely in the same language the user used."
    ),
    tools=[get_weather, get_current_time],
)

session_service = InMemorySessionService()
runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)


# ─────────────────────────────────────────────
# FastAPI Application & Schemas
# ─────────────────────────────────────────────
app = FastAPI(
    title="ADK Agent FastAPI Server",
    description="FastAPI server extension for Google ADK Agent supporting weather, time, and general chat.",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    message: str = Field(..., description="User prompt or query")
    session_id: Optional[str] = Field(None, description="Session ID. If not provided, a new session is created.")
    user_id: Optional[str] = Field(DEFAULT_USER_ID, description="User ID for the session.")


class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent response text")
    session_id: str = Field(..., description="Active session ID")


class SessionCreateRequest(BaseModel):
    user_id: Optional[str] = Field(DEFAULT_USER_ID, description="User ID for the new session")


class SessionCreateResponse(BaseModel):
    session_id: str
    user_id: str
    status: str


async def get_or_create_session(session_id: Optional[str], user_id: str) -> str:
    """Retrieves an existing session or creates a new one."""
    if session_id:
        try:
            existing = await session_service.get_session(
                app_name=APP_NAME, user_id=user_id, session_id=session_id
            )
            if existing is not None:
                return session_id
        except Exception:
            pass

    new_sid = session_id or f"session_{uuid.uuid4().hex[:8]}"
    await session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=new_sid
    )
    return new_sid


@app.get("/health")
async def health_check():
    """Health check endpoint to verify server status."""
    return {
        "status": "healthy",
        "app_name": APP_NAME,
        "agent": agent.name,
        "model": agent.model,
    }


@app.post("/sessions", response_model=SessionCreateResponse)
async def create_session(req: SessionCreateRequest = SessionCreateRequest()):
    """Explicitly create a new session."""
    user_id = req.user_id or DEFAULT_USER_ID
    sid = f"session_{uuid.uuid4().hex[:8]}"
    await session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=sid
    )
    return SessionCreateResponse(session_id=sid, user_id=user_id, status="created")


@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str, user_id: str = DEFAULT_USER_ID):
    """Retrieve details and event count for a session."""
    try:
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "session_id": session.id,
            "user_id": session.user_id,
            "event_count": len(session.events),
            "state": session.state,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session lookup failed: {e}")


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Main conversational endpoint powered by ADK Agent."""
    user_id = req.user_id or DEFAULT_USER_ID
    session_id = await get_or_create_session(req.session_id, user_id)

    try:
        content = types.Content(role="user", parts=[types.Part(text=req.message)])
        response_text = ""

        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response():
                if event.content and event.content.parts:
                    texts = [p.text for p in event.content.parts if hasattr(p, "text") and p.text]
                    if texts:
                        combined = "\n".join(texts).strip()
                        if "/*FINAL_ANSWER*/" in combined:
                            response_text = combined.split("/*FINAL_ANSWER*/")[-1].strip()
                        else:
                            response_text = combined

        if not response_text:
            response_text = "(No response)"

        return ChatResponse(response=response_text, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing agent query: {e}")


# ─────────────────────────────────────────────
# Server Entrypoint
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("=" * 65)
    print("  🚀 Starting ADK Agent FastAPI Server on http://127.0.0.1:8000")
    print("=" * 65)
    uvicorn.run(app, host="127.0.0.1", port=8000)

