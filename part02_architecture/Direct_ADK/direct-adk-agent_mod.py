import os
import sys
import warnings
from dotenv import load_dotenv

# Ensure UTF-8 output (prevents encoding issues on Windows console)
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load .env environment variables (override existing environment variables)
load_dotenv(override=True)

# Prevent duplicate warning between GOOGLE_API_KEY and GEMINI_API_KEY (GEMINI_API_KEY takes precedence)
os.environ.pop("GOOGLE_API_KEY", None)
#print("Currently loaded API KEY:", os.environ.get("GEMINI_API_KEY")[-5:]) 

# Suppress unnecessary warnings regarding ADK experimental features
warnings.filterwarnings("ignore", category=UserWarning)

import asyncio
import datetime
import requests
from zoneinfo import ZoneInfo

from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.planners import PlanReActPlanner

APP_NAME = "weather_time_app"
USER_ID = "user01"
SESSION_ID = "session01"

# ─────────────────────────────────────────────
# City name -> Latitude/Longitude/Timezone lookup (Open-Meteo Geocoding, free, no key required)
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
# Tool 1: Global weather lookup (Open-Meteo Weather API, free, no key required)
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
        "latitude": lat, "longitude": lon,
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
# Tool 2: Global current time lookup (Using Geocoding API timezone)
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
# Agent configuration
# ─────────────────────────────────────────────
# Note: Omitting planner allows the model's native Function Calling to handle
#       weather/time tools as well as general knowledge queries directly.

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

# ─────────────────────────────────────────────
# Session & Runner
# ─────────────────────────────────────────────
session_service = InMemorySessionService()
asyncio.run(session_service.create_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
))
runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)


# ─────────────────────────────────────────────
# Agent invocation function
# ─────────────────────────────────────────────
def call_agent(query: str) -> str:
    try:
        content = types.Content(role="user", parts=[types.Part(text=query)])
        events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)
        for event in events:
            # Debug: verify event structure (uncomment if needed)
            # print(f"[DEBUG] is_final={event.is_final_response()}, author={event.author}, content={event.content}")
            if event.is_final_response():
                if event.content and event.content.parts:
                    # Return the first part containing text
                    texts = [p.text for p in event.content.parts if hasattr(p, "text") and p.text]
                    if texts:
                        response_text = "\n".join(texts).strip()
                        if "/*FINAL_ANSWER*/" in response_text:
                            return response_text.split("/*FINAL_ANSWER*/")[-1].strip()
                        return response_text
                # If content is empty — continue loop even if only author info is present
        return "(No response)"
    except Exception as e:
        return f"An error occurred while processing the request: {e}"


# ─────────────────────────────────────────────
# Interactive loop
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60) 
    print("  🌍 General Query, Weather & Time Agent (Worldwide Cities Supported)")
    print("  Type 'quit', 'exit', or 'q' to terminate.")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEnding conversation.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Ending conversation.")
            break

        answer = call_agent(user_input)
        print(f"\n🤖 Agent: {answer}")
