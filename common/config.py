"""실습 공통 설정: 모델 이름과 .env 로딩."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)

if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() in ("TRUE", "1"):
    os.environ.pop("GOOGLE_API_KEY", None)
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
else:
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
    os.environ.pop("GOOGLE_CLOUD_LOCATION", None)

# 슬라이드와 adk.dev 퀵스타트가 사용하는 별칭. 운영에서는 버전 고정을 권장.
MODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")


def has_llm_credentials() -> bool:
    """Gemini 호출에 필요한 인증 정보가 있는지 확인한다."""
    if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() in ("TRUE", "1"):
        return bool(os.getenv("GOOGLE_CLOUD_PROJECT"))
    key = os.getenv("GOOGLE_API_KEY", "")
    return bool(key) and not key.startswith("<")
