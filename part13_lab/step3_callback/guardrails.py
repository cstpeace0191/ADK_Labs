"""실습 3단계 가드레일: 학번·주민번호·전화번호 등 개인정보 입력 차단."""
import re

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

PII_PATTERNS = {
    "주민등록번호": re.compile(r"\d{6}-?[1-4]\d{6}"),
    "학번": re.compile(r"(학번\s*[:은는]?\s*\d{6,10})|\b20\d{6}\b"),
    "전화번호": re.compile(r"01[016789]-?\d{3,4}-?\d{4}"),
    "비밀번호": re.compile(r"(비밀번호|패스워드|password)\s*[:은는]?\s*\S+", re.I),
}


def detect_pii(text: str) -> list[str]:
    return [name for name, pat in PII_PATTERNS.items() if pat.search(text or "")]


def block_pii(callback_context: CallbackContext, llm_request: LlmRequest):
    """before_model_callback: 마지막 사용자 메시지에 개인정보가 있으면 LLM 호출 없이 차단."""
    last_user = next((c for c in reversed(llm_request.contents or []) if c.role == "user"), None)
    text = "".join(p.text or "" for p in (last_user.parts or [])) if last_user else ""
    found = detect_pii(text)
    if found:
        callback_context.state["pii_blocked"] = callback_context.state.get("pii_blocked", 0) + 1
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(
            text=f"개인정보({', '.join(found)})는 입력하지 마세요. 학번은 로그인 정보로 자동 확인됩니다.")]))
    return None


def validate_course_code(tool, args, tool_context):
    """before_tool_callback: 과목 코드 형식 검증 (예: CS101)."""
    code = args.get("course_code")
    if code is not None and not re.fullmatch(r"[A-Za-z]{2}\d{3}", code):
        return {"status": "error", "error_message": f"과목 코드 형식 오류: {code} (예: CS101)"}
    return None
