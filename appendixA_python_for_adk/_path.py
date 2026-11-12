"""스크립트 실행 시 실습 루트(common 패키지)를 import 경로에 추가하고 .env를 읽는다."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common.bootstrap  # noqa: E402,F401
