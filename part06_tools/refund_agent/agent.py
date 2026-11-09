"""강의노트 Part 6 슬라이드 77: 사람 확인이 필요한 도구 — LongRunningFunctionTool.

도구는 즉시 'pending' 을 반환하고, 외부 시스템(관리자)의 승인 결과는 나중에
같은 function_call id 로 FunctionResponse 를 보내 주입한다 (run_tools.py refund 참고).
"""
import itertools
import os

from google.adk import Agent
from google.adk.tools import LongRunningFunctionTool

_ticket_seq = itertools.count(1)


def create_ticket(order_id: str, amount: int) -> str:
    return f"TICKET-{next(_ticket_seq):04d}"


def request_refund(order_id: str, amount: int) -> dict:
    """환불 요청을 생성하고 관리자 승인을 기다린다.

    Args:
        order_id: 주문 번호 (예: "ORD-1001")
        amount: 환불 금액(원)
    """
    ticket = create_ticket(order_id, amount)
    return {"status": "pending", "ticket": ticket, "order_id": order_id, "amount": amount}


refund_tool = LongRunningFunctionTool(func=request_refund)

root_agent = Agent(
    name="refund_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    instruction="환불 요청은 request_refund 로 접수한다. 결과가 pending이면 승인 대기 중이라고 안내하고, "
                "이후 승인/거절 결과가 오면 그 결과를 사용자에게 알린다.",
    tools=[refund_tool],
)
