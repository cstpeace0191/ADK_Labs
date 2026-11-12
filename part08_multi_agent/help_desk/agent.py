"""강의노트 Part 8 슬라이드 92: sub_agents 와 LLM 위임(transfer_to_agent).

부모 프롬프트에 하위 에이전트 목록 + description 이 자동 포함되고,
LLM 이 transfer_to_agent(name) 를 호출하면 대화 제어권이 하위 에이전트로 넘어간다(chat 모드).
"""
import os

from google.adk import Agent

MODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")


def lookup_invoice(invoice_id: str) -> dict:
    """청구서 상태를 조회한다.

    Args:
        invoice_id: 청구서 번호 (예: "INV-2026-001")
    """
    db = {"INV-2026-001": {"amount": 59000, "status": "결제 실패", "reason": "카드 한도 초과"},
          "INV-2026-002": {"amount": 12000, "status": "결제 완료"}}
    if invoice_id in db:
        return {"status": "success", "invoice": db[invoice_id]}
    return {"status": "error", "error_message": f"{invoice_id} 없음"}


billing = Agent(
    name="billing_agent", model=MODEL,
    description="청구서, 결제 실패, 환불 문의를 처리한다.",
    instruction="결제 관련 질문만 답하라. 청구서 번호가 있으면 lookup_invoice 로 조회한다. "
                "결제와 무관한 질문이면 help_desk 로 되돌려라.",
    tools=[lookup_invoice],
)

tech = Agent(
    name="tech_agent", model=MODEL,
    description="로그인 오류, 앱 버그 등 기술 문제를 처리한다.",
    instruction="재현 절차를 먼저 묻고 해결책을 제시하라. 기술 문제가 아니면 help_desk 로 되돌려라.",
)

root_agent = Agent(
    name="help_desk", model=MODEL,
    instruction="요청을 분류해 가장 적합한 담당에게 넘겨라. 일반 인사는 직접 답하라.",
    sub_agents=[billing, tech],
)
