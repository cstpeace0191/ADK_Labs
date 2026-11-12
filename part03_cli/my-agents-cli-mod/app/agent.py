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

"""AI assistant that provides current local times and weather worldwide and answers general questions."""
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

# Load environment variables from .env.
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

# WMO weather code descriptions.
WMO_WEATHER_CODES = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Light rain showers",
    81: "Rain showers",
    82: "Heavy rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}

# Default fallback data for network outages or offline use.
_OFFLINE = {
    "seoul": ("Seoul, South Korea", 37.5665, 126.9780, "Asia/Seoul"),
    "busan": ("Busan, South Korea", 35.1796, 129.0756, "Asia/Seoul"),
    "jeju": ("Jeju, South Korea", 33.4996, 126.5312, "Asia/Seoul"),
    "tokyo": ("Tokyo, Japan", 35.6762, 139.6503, "Asia/Tokyo"),
    "new york": ("New York, United States", 40.7128, -74.0060, "America/New_York"),
    "paris": ("Paris, France", 48.8566, 2.3522, "Europe/Paris"),
    "london": ("London, United Kingdom", 51.5074, -0.1278, "Europe/London"),
    "san francisco": ("San Francisco, United States", 37.7749, -122.4194, "America/Los_Angeles"),
    "sf": ("San Francisco, United States", 37.7749, -122.4194, "America/Los_Angeles"),
    "sydney": ("Sydney, Australia", -33.8688, 151.2093, "Australia/Sydney"),
}


def _get_json(url: str, timeout: int = 5) -> dict:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def geocode(location: str) -> dict:
    """Find a city or region worldwide and return its coordinates and timezone.

    Args:
        location: City or region to search for (for example, 'Seoul', 'Tokyo', 'New York', 'Paris', or 'San Francisco').

    Returns:
        A dict containing status, location, display_name, latitude, longitude, and timezone.
    """
    cleaned = location.strip()
    key = cleaned.lower()
    search_query = cleaned

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

    # Use fallback data when the request fails or offline mode is enabled.
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

    return {"status": "error", "message": f"Could not find coordinates and timezone for '{location}'"}


def _resolve(location: str, latitude: float | None, longitude: float | None):
    """Resolve a city name or coordinates to a display name, latitude, longitude, and timezone."""
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
    """Get the current local time for a city or coordinates.

    Args:
        location: City or region (for example, 'Seoul', 'Tokyo', 'New York', 'Paris', or 'San Francisco').
        query: Alternative parameter for location.
        latitude: Latitude (optional).
        longitude: Longitude (optional).

    Returns:
        A dict containing status, location, timezone, current_time, and message.
    """
    target = location.strip() or query.strip()
    res = _resolve(target, latitude, longitude)
    if res is None:
        return {"status": "error", "message": f"Could not resolve a city name or coordinates to look up the time: '{target}'"}

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
        "message": f"The local time in '{name}' (latitude {lat:.4f}, longitude {lng:.4f}, timezone {tz_name}) is {formatted_time}.",
    }


def get_weather(
    location: str = "",
    query: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Get current weather and temperature for a city or coordinates.

    Args:
        location: City or region (for example, 'Seoul', 'Paris', 'Tokyo', 'New York', or 'San Francisco').
        query: Alternative parameter for location.
        latitude: Latitude (optional).
        longitude: Longitude (optional).

    Returns:
        A dict containing status, location, condition, temperature, feels_like, humidity, wind_speed, and message.
    """
    target = location.strip() or query.strip()
    res = _resolve(target, latitude, longitude)
    if res is None:
        return {"status": "error", "message": f"Could not resolve a city name or coordinates to look up the weather: '{target}'"}

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
            condition = WMO_WEATHER_CODES.get(code, "Unknown")
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
                    f"Current weather in '{name}':\n"
                    f"- Condition: {condition}\n"
                    f"- Temperature: {temp}°C (feels like: {feels_like}°C)\n"
                    f"- Humidity: {humidity}%\n"
                    f"- Wind speed: {wind_speed} km/h"
                ),
            }
        except Exception:
            pass

    # Return default offline data if the request fails.
    return {
        "status": "success",
        "location": name,
        "latitude": lat,
        "longitude": lng,
        "condition": "Clear",
        "temperature": 18.0,
        "apparent_temperature": 17.0,
        "humidity": 45,
        "wind_speed": 7.0,
        "source": "offline_fallback",
        "message": f"Current weather in '{name}' (offline fallback): Clear, temperature 18.0°C, humidity 45%",
    }


INSTRUCTION = """You are a friendly, capable, and accurate general-purpose AI assistant.

[Core behavior]
1. Questions about local time and weather anywhere in the world:
   - When the user asks for the current time, weather, temperature, or conditions in a city or region, actively use the available tools (`geocode`, `get_current_time`, `get_weather`).
   - Use `geocode` first when coordinates or a timezone are needed, or pass a city name directly to `get_current_time` or `get_weather`.
   - Combine the returned local time, temperature, feels-like temperature, conditions (clear, cloudy, rain, etc.), humidity, and wind speed into a natural, friendly English answer.

2. All other questions:
   - Do not call tools for questions that do not require them, including greetings, casual conversation, general knowledge, science, history, humanities, programming, writing, translation, summarization, and advice.
   - Use your knowledge to answer questions helpfully, thoroughly, and kindly.
"""

root_agent = Agent(
    # Keep in sync with create_params.root_agent_name in agents-cli-manifest.yaml:
    name="my_agents_cli_mod",
    description="A general-purpose assistant that retrieves current local time and weather worldwide and answers general questions helpfully.",
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
