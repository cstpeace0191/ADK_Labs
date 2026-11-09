"""각 run_*.py 맨 위에서 import 하면 루트를 sys.path에 넣고 .env를 읽는다."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:  # Windows 콘솔 한글 출력
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from common.config import MODEL, has_llm_credentials  # noqa: E402,F401


def _install_gemini_retry() -> None:
    """무료 등급의 분당 호출 한도(429)·일시 오류(5xx)를 자동 재시도한다.

    에이전트 코드는 슬라이드처럼 model="gemini-..." 문자열을 그대로 쓴다.
    ADK는 이 문자열을 LLMRegistry로 Gemini 객체로 바꾸므로, 재시도 옵션을 가진
    하위 클래스를 같은 패턴으로 등록해 둔다. 끄려면 ADK_LAB_RETRY=0.
    """
    import os
    if os.getenv("ADK_LAB_RETRY", "1") == "0":
        return
    from google.adk.models.google_llm import Gemini
    from google.adk.models.registry import LLMRegistry
    from google.genai import types

    class RetryGemini(Gemini):
        retry_options: types.HttpRetryOptions | None = types.HttpRetryOptions(
            # 10s → 20s → 40s: 분당 한도(RPM)를 넘기기에 충분하다. 일일 한도(RPD)는 재시도로 풀리지 않는다.
            attempts=4, initial_delay=10, max_delay=40, exp_base=2,
            http_status_codes=[429, 500, 502, 503, 504])

    LLMRegistry.register(RetryGemini)
    LLMRegistry.resolve.cache_clear()


_install_gemini_retry()


def require_llm() -> None:
    if not has_llm_credentials():
        print("⚠ GOOGLE_API_KEY(또는 Vertex AI 설정)가 없습니다. 루트의 .env.example을 .env로 복사해 채우세요.")
        sys.exit(0)
