"""강의노트 Part 6 슬라이드 72: Function Tool — 시그니처와 docstring이 곧 API.

- 타입 힌트 필수, docstring에 인자 형식·예시
- 예외 대신 status · error_message 반환
- ToolContext는 스키마에서 자동 제외되고, state 쓰기는 state_delta로 기록된다
- 부작용(결제)은 require_confirmation 으로 사람 확인 (슬라이드 77 '도구 확인')
"""
import os

from google.adk import Agent
from google.adk.tools import FunctionTool, ToolContext

CATALOG = {"SKU-123": ("무선 마우스", 25000), "SKU-456": ("기계식 키보드", 89000),
           "SKU-789": ("USB-C 허브", 39000)}


def list_products() -> dict:
    """판매 중인 상품 목록을 반환한다."""
    return {"status": "success",
            "products": [{"id": k, "name": n, "price": p} for k, (n, p) in CATALOG.items()]}


def add_to_cart(item_id: str, qty: int, tool_context: ToolContext) -> dict:
    """장바구니에 상품을 담는다.

    Args:
        item_id: 상품 ID (예: "SKU-123")
        qty: 수량, 1 이상
    Returns:
        status와 현재 장바구니 개수
    """
    if qty < 1:
        return {"status": "error", "error_message": "qty>=1"}
    if item_id not in CATALOG:
        return {"status": "error", "error_message": f"없는 상품: {item_id}"}
    cart = tool_context.state.get("cart", [])
    cart.append({"id": item_id, "qty": qty})
    tool_context.state["cart"] = cart  # state_delta로 기록
    return {"status": "success", "count": len(cart)}


def view_cart(tool_context: ToolContext) -> dict:
    """현재 장바구니와 합계 금액을 반환한다."""
    cart = tool_context.state.get("cart", [])
    total = sum(CATALOG[c["id"]][1] * c["qty"] for c in cart)
    return {"status": "success", "cart": cart, "total": total}


def checkout(tool_context: ToolContext) -> dict:
    """장바구니를 결제한다. (되돌리기 어려운 행동 → 실행 전 사람 확인)"""
    cart = tool_context.state.get("cart", [])
    if not cart:
        return {"status": "error", "error_message": "장바구니가 비어 있음"}
    total = sum(CATALOG[c["id"]][1] * c["qty"] for c in cart)
    tool_context.state["cart"] = []
    return {"status": "success", "paid": total, "order_id": "ORD-0001"}


root_agent = Agent(
    name="shop_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    description="상품 조회와 장바구니를 관리하는 쇼핑 도우미",
    instruction="상품은 list_products, 담기는 add_to_cart, 확인은 view_cart, 결제는 checkout 도구를 쓴다. "
                "상품 이름으로 요청하면 list_products로 ID를 찾아 처리한다. "
                "결제 요청을 받으면 되묻지 말고 바로 checkout을 호출한다(사용자 확인은 ADK가 받는다).",
    tools=[list_products, add_to_cart, view_cart,
           FunctionTool(checkout, require_confirmation=True)],
)
