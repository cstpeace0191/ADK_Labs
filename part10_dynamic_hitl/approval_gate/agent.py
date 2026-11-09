"""강의노트 Part 10 슬라이드 106: 승인 게이트 패턴 — 재실행형 RequestInput + 구조화 응답으로 라우팅 (LLM 없음).

@node(rerun_on_resume=True) 노드는 재개 시 처음부터 다시 실행되며,
ctx.resume_inputs[interrupt_id] 로 사람 응답을 읽는다.
감사 로그: 승인 기록을 state["audit_log"] 에 남긴다.
"""
from datetime import datetime

from google.adk import Context, Event, Workflow
from google.adk.events import RequestInput
from google.adk.workflow import node
from pydantic import BaseModel


class Decision(BaseModel):
    approve: bool
    note: str = ""


def load_refund(node_input: str):
    return {"order_id": node_input.strip(), "amount": 450000, "policy_flags": ["구매 후 25일", "개봉 상품"]}


@node(rerun_on_resume=True)
async def escalate_to_human(ctx: Context, node_input: dict):
    answer = ctx.resume_inputs.get("refund_review")
    if answer is None:  # 첫 실행: 질문하고 멈춤
        yield RequestInput(interrupt_id="refund_review",
                           message="환불을 승인할까요?",
                           payload=node_input,  # 판단 근거(주문·정책 위반 항목)
                           response_schema=Decision)
        return
    decision = Decision.model_validate(answer)
    ctx.state["audit_log"] = ctx.state.get("audit_log", []) + [{
        "order_id": node_input["order_id"], "approve": decision.approve,
        "note": decision.note, "at": datetime.now().isoformat(timespec="seconds")}]
    yield Event(output={**node_input, "note": decision.note},
                route="APPROVE" if decision.approve else "DENY")


def approved(node_input: dict):
    return Event(message=f"환불 승인: {node_input['order_id']} {node_input['amount']:,}원 ({node_input['note']})")


def denied(node_input: dict):
    return Event(message=f"환불 거절: {node_input['order_id']} ({node_input['note']})")


root_agent = Workflow(name="approval_gate", edges=[
    ("START", load_refund, escalate_to_human),
    (escalate_to_human, {"APPROVE": approved, "DENY": denied}),
])
