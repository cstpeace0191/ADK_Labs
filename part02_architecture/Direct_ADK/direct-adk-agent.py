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

import asyncio
import datetime
import requests
from zoneinfo import ZoneInfo

from google.genai import types
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

APP_NAME = "weather_time_app"
USER_ID = "user01"
SESSION_ID = "session01"


# 1. Define weather retrieval tool
def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.
    
    Args:
        city (str): The name of the city for which to retrieve the weather report.
        
    Returns:
        dict: status and result or error msg.
    """
    city_lower = city.lower()
    if "new york" in city_lower:
        return {
            "status": "success",
            "report": "The weather in New York is sunny with a temperature of 25 degrees Celsius.",
        }
    elif "seoul" in city_lower:
        return {
            "status": "success",
            "report": "Seoul is experiencing clear skies with a temperature of 20 degrees Celsius.",
        }
    elif "hanoi" in city_lower:
        return {
            "status": "success",
            "report": "Hanoi is experiencing cloudy skies with a temperature of 28 degrees Celsius.",
        }
    elif "islamabad" in city_lower:
        return {
            "status": "success",
            "report": "Islamabad is experiencing clear skies with a temperature of 22 degrees Celsius.",
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }


# 2. Define current time retrieval tool
def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city.
    
    Args:
        city (str): The name of the city for which to retrieve the current time.
        
    Returns:
        dict: status and result or error msg.
    """
    city_lower = city.lower()
    if "new york" in city_lower:
        tz_identifier = "America/New_York"
    elif "seoul" in city_lower:
        tz_identifier = "Asia/Seoul"
    elif "hanoi" in city_lower:
        tz_identifier = "Asia/Bangkok"
    elif "islamabad" in city_lower:
        tz_identifier = "Asia/Karachi"
    else:
        return {
            "status": "error",
            "error_message": f"Sorry, I don't have timezone information for {city}.",
        }
    
    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = f"The current time in {city} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
    return {"status": "success", "report": report}


# 3. Configure root Agent and bind tools
root_agent = Agent(
    name="weather_time_agent",
    model="gemini-3.5-flash",  # Specify Gemini model to use
    description="Agent to answer questions about the time and weather in a city.",
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city. "
        "Use the provided tools when necessary to fetch accurate information."
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
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)


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
    print("  🤖 AI Agent (Real-time Weather & Time Lookup & General Chat)")
    print("  You can ask questions in English or Korean.")
    print("  (Supported cities: Seoul, Hanoi, Islamabad, New York)")
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
