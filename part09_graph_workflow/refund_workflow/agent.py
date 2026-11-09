"""강의노트 Part 9 슬라이드 99: 사례 ① 환불 처리 그래프 (Google Cloud 블로그 패턴 재구성).

START → (fetch_order, fetch_payment, fetch_history) 병렬 조회 → join_case → route_refund
route_refund ─ AUTO_APPROVE  → approve_notice (Agent: 안내문 작성)
             ├ MANUAL_REVIEW → escalate_to_human (RequestInput: 사람 승인) → APPROVE/DENY
             └ DENY          → denial_notice  (Agent: 안내문 작성)

설계 교훈: 조회는 병렬, 규칙은 코드, 모델은 문안 작성에만, 애매하면 사람.
Gemini 키가 없으면 안내문 노드가 템플릿 함수로 대체되어 그래프 전체를 오프라인으로 실습할 수 있다.
입력 예: ORD-1 (소액·자동승인) / ORD-2 (고액·사람검토) / ORD-3 (환불이력 과다·거절)
"""
import os

from google.adk import Agent, Context, Event, Workflow
from google.adk.events import RequestInput
from google.adk.workflow import JoinNode, node
from pydantic import BaseModel

MODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")
_KEY = os.getenv("GOOGLE_API_KEY", "")
USE_LLM = (bool(_KEY) and not _KEY.startswith("<")) or \
    os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE"

ORDERS = {"ORD-1": {"item": "무선 마우스", "amount": 25000, "days_since": 3},
          "ORD-2": {"item": "노트북", "amount": 1890000, "days_since": 10},
          "ORD-3": {"item": "키보드", "amount": 89000, "days_since": 5}}
PAYMENTS = {"ORD-1": "card", "ORD-2": "card", "ORD-3": "bank"}
HISTORY = {"ORD-1": 0, "ORD-2": 1, "ORD-3": 4}  # 최근 90일 환불 횟수


# ── 병렬 조회 (함수 노드)
def fetch_order(node_input: str):
    oid = node_input.strip()
    return {"order_id": oid, **ORDERS.get(oid, {"item": "?", "amount": 0, "days_since": 999})}


def fetch_payment(node_input: str):
    return {"method": PAYMENTS.get(node_input.strip(), "unknown")}


def fetch_history(node_input: str):
    return {"refunds_90d": HISTORY.get(node_input.strip(), 0)}


join_case = JoinNode(name="join_case")


# ── 규칙 라우터 (LLM 비용 0)
def route_refund(node_input: dict):
    case = {**node_input["fetch_order"], **node_input["fetch_payment"], **node_input["fetch_history"]}
    if case["refunds_90d"] >= 3 or case["days_since"] > 30:
        route = "DENY"
    elif case["amount"] <= 100000:
        route = "AUTO_APPROVE"
    else:
        route = "MANUAL_REVIEW"
    return Event(output=case, route=route)


# ── 사람 승인 게이트 (Part 10 슬라이드 106 패턴)
class Decision(BaseModel):
    approve: bool
    note: str = ""


@node(rerun_on_resume=True)
async def escalate_to_human(ctx: Context, node_input: dict):
    answer = ctx.resume_inputs.get("refund_review")
    if answer is None:  # 첫 실행: 질문하고 멈춘다
        yield RequestInput(interrupt_id="refund_review",
                           message="고액 환불입니다. 승인할까요? (approve: true/false, note)",
                           payload=node_input, response_schema=Decision)
        return
    yield Event(output={**node_input, "note": answer.get("note", "")},
                route="APPROVE" if answer.get("approve") else "DENY")


# ── 안내문 작성: LLM 노드 또는 템플릿
if USE_LLM:
    approve_notice = Agent(
        name="approve_notice", model=MODEL, mode="single_turn",
        instruction="입력된 환불 건 정보로 고객에게 보낼 환불 승인 안내문을 3문장으로 정중하게 써라.")
    denial_notice = Agent(
        name="denial_notice", model=MODEL, mode="single_turn",
        instruction="입력된 환불 건 정보로 환불 거절 안내문을 3문장으로 정중하게 쓰고, 사유를 포함하라.")
else:
    def approve_notice(node_input: dict):
        return Event(message=f"[승인] {node_input['order_id']} {node_input['item']} "
                             f"{node_input['amount']:,}원 환불이 승인되었습니다. {node_input.get('note', '')}")

    def denial_notice(node_input: dict):
        return Event(message=f"[거절] {node_input['order_id']} 환불이 거절되었습니다 "
                             f"(최근 환불 {node_input['refunds_90d']}회, 구매 후 {node_input['days_since']}일). "
                             f"{node_input.get('note', '')}")

root_agent = Workflow(name="refund_workflow", edges=[
    ("START", (fetch_order, fetch_payment, fetch_history), join_case, route_refund),
    (route_refund, {"AUTO_APPROVE": approve_notice,
                    "MANUAL_REVIEW": escalate_to_human,
                    "DENY": denial_notice}),
    (escalate_to_human, {"APPROVE": approve_notice, "DENY": denial_notice}),
])
