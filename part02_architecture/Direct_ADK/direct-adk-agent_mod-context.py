import os
import sys
import json
import warnings
from typing import Optional
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

import asyncio
import datetime
import requests
from zoneinfo import ZoneInfo

from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.plugins import BasePlugin
from google.adk.models import LlmRequest, LlmResponse

APP_NAME = "weather_time_context_app"
USER_ID = "user01"
SESSION_ID = "session01"


# ─────────────────────────────────────────────
# Helper: Extract and dump raw Content to dictionary
# ─────────────────────────────────────────────
def dump_raw_content(content) -> dict:
    """Serializes a types.Content or similar object to its raw dictionary representation."""
    if content is None:
        return {}
    if hasattr(content, "model_dump"):
        return content.model_dump(exclude_none=True)
    if hasattr(content, "to_json_dict"):
        return content.to_json_dict()
    if isinstance(content, dict):
        return content
    return {"raw": str(content)}


# ─────────────────────────────────────────────
# Helper: Inspect and explain Thought & Thought Signature
# ─────────────────────────────────────────────
def explain_thought_and_signature(content, label: str = "Model Output"):
    """Extracts and prints detailed explanations for internal reasoning thoughts
    and cryptographic thought_signatures found in Content parts."""
    if not content or not hasattr(content, "parts") or not content.parts:
        return

    found_thought = False
    found_signature = False

    for idx, part in enumerate(content.parts, 1):
        is_thought = getattr(part, "thought", False)
        thought_sig = getattr(part, "thought_signature", None)
        text = getattr(part, "text", None)

        if is_thought and text:
            found_thought = True
            print(f"\n🧠 [Internal Reasoning / Chain-of-Thought (Part #{idx})]:")
            print("─" * 70)
            print(text.strip())
            print("─" * 70)

        if thought_sig is not None:
            found_signature = True
            sig_bytes = thought_sig if isinstance(thought_sig, bytes) else str(thought_sig).encode()
            print(f"\n🔐 [Thought Signature Inspection (Part #{idx})]:")
            print(f"   • Field Name  : 'thought_signature'")
            print(f"   • What It Is  : Google Gemini opaque cryptographic integrity token (serialized protobuf bytes).")
            print(f"   • Why It Exists: Signs the model's preceding reasoning (thought) and function calls.")
            print(f"                   When conversation history is sent back to Gemini in subsequent turns,")
            print(f"                   this signature validates that intermediate model reasoning has NOT")
            print(f"                   been modified, injected, or tampered with by the user or client.")
            print(f"   • Byte Length : {len(sig_bytes)} bytes")
            print(f"   • Hex Preview : {sig_bytes[:32].hex()}... (truncated)")


# ─────────────────────────────────────────────
# Plugin: Raw Context Window & Thought Inspector
# ─────────────────────────────────────────────
class ContextDisplayPlugin(BasePlugin):
    """Plugin to display the exact, uncompressed raw context window
    (system prompt, tool declarations, conversation history, model outputs,
    and internal thoughts with thought_signatures) on every LLM invocation."""

    def __init__(self):
        super().__init__(name="raw_context_display_plugin")
        self.call_count = 0

    async def before_model_callback(self, *, callback_context, llm_request: LlmRequest) -> Optional[LlmResponse]:
        self.call_count += 1
        print("\n" + "=" * 80)
        print(f"🔍 [LLM Call #{self.call_count} - Exact Context Window Sent to Model]")
        print(f"Target Model: {llm_request.model}")
        print("=" * 80)

        # 1. Exact System Instruction / Prompt
        print("\n📌 [1. System Instruction]:")
        print("-" * 80)
        sys_inst = None
        if hasattr(llm_request.config, "system_instruction") and llm_request.config.system_instruction:
            inst_obj = llm_request.config.system_instruction
            if isinstance(inst_obj, str):
                sys_inst = inst_obj
            elif hasattr(inst_obj, "parts") and inst_obj.parts:
                sys_inst = "\n".join(p.text for p in inst_obj.parts if getattr(p, "text", None))
            elif hasattr(inst_obj, "model_dump"):
                sys_inst = json.dumps(inst_obj.model_dump(exclude_none=True), indent=2, ensure_ascii=False, default=str)
            else:
                sys_inst = str(inst_obj)

        if sys_inst:
            print(sys_inst.strip())
        else:
            print("(None)")

        # 2. Available Tool Declarations in Context
        print("\n🛠️  [2. Available Tools in Context]:")
        print("-" * 80)
        tools_dict = getattr(llm_request, "tools_dict", None) or {}
        if tools_dict:
            for tool_name, tool_instance in tools_dict.items():
                desc = getattr(tool_instance, "description", "")
                print(f"  • {tool_name}: {desc.strip() if desc else '(No description)'}")
        else:
            print("(None)")

        # 3. Exact Context Messages / Conversation History (Raw as-is JSON)
        contents = getattr(llm_request, "contents", []) or []
        print(f"\n📜 [3. Context Messages / Conversation History ({len(contents)} messages)]:")
        print("-" * 80)
        raw_contents = [dump_raw_content(c) for c in contents]
        print(json.dumps(raw_contents, indent=2, ensure_ascii=False, default=str))

        print("=" * 80 + "\n")
        return None

    async def after_model_callback(self, *, callback_context, llm_response: LlmResponse) -> Optional[LlmResponse]:
        print("-" * 80)
        print(f"📥 [LLM Call #{self.call_count} - Exact Model Response / Action Generated]")
        print("-" * 80)

        if getattr(llm_response, "content", None):
            raw_response = dump_raw_content(llm_response.content)
            print(json.dumps(raw_response, indent=2, ensure_ascii=False, default=str))

            # Explain thoughts and thought_signatures if present
            explain_thought_and_signature(llm_response.content, label="Generated Model Response")
        else:
            print("(No content generated)")

        usage = getattr(llm_response, "usage_metadata", None)
        if usage:
            prompt_tokens = getattr(usage, "prompt_token_count", "N/A")
            cand_tokens = getattr(usage, "candidates_token_count", "N/A")
            total_tokens = getattr(usage, "total_token_count", "N/A")
            print(f"\n📊 Token Usage: Prompt={prompt_tokens} | Output={cand_tokens} | Total={total_tokens}")

        print("-" * 80 + "\n")
        return None


# ─────────────────────────────────────────────
# Tool 1: Geocoding Lookup (Open-Meteo Geocoding)
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
# Tool 2: Weather Lookup (Open-Meteo Weather API)
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
# Tool 3: Current Time Lookup (Geocoding API timezone)
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
# Agent & Runner Configuration
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
    generate_content_config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(include_thoughts=True)
    ),
)

session_service = InMemorySessionService()
asyncio.run(session_service.create_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
))

context_plugin = ContextDisplayPlugin()
runner = Runner(
    agent=agent,
    app_name=APP_NAME,
    session_service=session_service,
    plugins=[context_plugin],
)


# ─────────────────────────────────────────────
# Agent invocation function
# ─────────────────────────────────────────────
def call_agent(query: str) -> str:
    try:
        content = types.Content(role="user", parts=[types.Part(text=query)])
        events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)
        for event in events:
            if event.is_final_response():
                if event.content and event.content.parts:
                    # Filter out internal thought parts so user only sees the final conversational response
                    texts = [
                        p.text for p in event.content.parts
                        if hasattr(p, "text") and p.text and not getattr(p, "thought", False)
                    ]
                    if texts:
                        response_text = "\n".join(texts).strip()
                        if "/*FINAL_ANSWER*/" in response_text:
                            return response_text.split("/*FINAL_ANSWER*/")[-1].strip()
                        return response_text
        return "(No response)"
    except Exception as e:
        return f"An error occurred while processing the request: {e}"


# ─────────────────────────────────────────────
# Interactive loop
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 80)
    print("  🔍 Raw Context Window & Thought Inspector Agent")
    print("  • System prompt, tools, conversation history, and model outputs are printed as raw JSON.")
    print("  • Internal model reasoning (thoughts) and cryptographic thought_signatures are explained.")
    print("  Type 'quit', 'exit', or 'q' to terminate.")
    print("=" * 80)

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
