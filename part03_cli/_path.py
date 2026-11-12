"""Add the lab root to the import path and load .env when running a script."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common.bootstrap  # noqa: E402,F401
