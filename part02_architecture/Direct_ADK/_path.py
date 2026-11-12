"""Adds lab root (common package) and agent folders to import path and loads .env on script execution.

Direct_ADK/ is two levels below the lab root (ADK_Labs/part02_architecture/Direct_ADK),
and agents used by run_events.py / run_memory_layers.py are located in ../adk-based_Agent/.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))           # ADK_Labs (common package)
sys.path.insert(1, str(_HERE.parent / "adk-based_Agent"))  # chat_time_weather_agent / memory_layers_agent
import common.bootstrap  # noqa: E402,F401
