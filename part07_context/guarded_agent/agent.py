"""강의노트 Part 7 슬라이드 83~84: Callback — 금칙어 가드레일 + 도구 인자 검증 + 로깅 Plugin.

규칙: before_* 콜백이 값을 반환하면 원래 단계(LLM 호출/도구 실행)는 건너뛴다. None이면 진행.
"""
import os

from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import ToolContext
from google.genai import types

BLOCK = ["주민등록번호", "비밀번호"]


def add_to_cart(item_id: str, qty: int, tool_context: ToolContext) -> dict:
    """장바구니에 상품을 담는다.

    Args:
        item_id: 상품 ID (예: "SKU-123")
        qty: 수량, 1 이상
    """
    cart = tool_context.state.get("cart", [])
    cart.append({"id": item_id, "qty": qty})
    tool_context.state["cart"] = cart
    return {"status": "success", "count": len(cart)}


# ── before_model_callback: 프롬프트 가드레일 (LLM 호출 자체를 막는다)
def guard(callback_context: CallbackContext, llm_request: LlmRequest):
    last = llm_request.contents[-1] if llm_request.contents else None
    text = "".join(p.text or "" for p in (last.parts if last and last.parts else []))
    if any(w in text for w in BLOCK):
        callback_context.state["blocked_count"] = callback_context.state.get("blocked_count", 0) + 1
        return LlmResponse(content=types.Content(
            role="model", parts=[types.Part(text="민감정보는 처리할 수 없습니다.")]))
    return None  # 통과


# ── before_tool_callback: 인자 검증·차단 (dict를 반환하면 그 값이 도구 결과가 된다)
def check_args(tool, args, tool_context):
    if tool.name == "add_to_cart" and args.get("qty", 0) > 10:
        return {"status": "error", "error_message": "최대 10개"}
    return None


# ── after_model_callback: 응답 후처리 (전화번호 마스킹)
def mask_phone(callback_context: CallbackContext, llm_response: LlmResponse):
    import re
    if not (llm_response.content and llm_response.content.parts):
        return None
    changed = False
    for p in llm_response.content.parts:
        if p.text:
            new = re.sub(r"01[016789]-?\d{3,4}-?\d{4}", "010-****-****", p.text)
            changed |= new != p.text
            p.text = new
    return llm_response if changed else None


root_agent = Agent(
    name="guarded_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    instruction="쇼핑 도우미. 상품 담기 요청은 add_to_cart 로 처리하고 결과를 그대로 알려라.",
    tools=[add_to_cart],
    before_model_callback=guard,
    before_tool_callback=check_args,
    after_model_callback=mask_phone,
)
