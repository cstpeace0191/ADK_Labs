"""강의노트 Part 9 슬라이드 105: 사례 ② ambient-expense-agent (이벤트 → 코드 분기 → LLM → 승인).

START → parse_expense_email → route_by_amount ─ AUTO_APPROVE ($100 미만) → auto_approve
                                               └ NEEDS_REVIEW → review_agent(LLM) → request_approval(사람) → process_decision

입력 예 (Pub/Sub 메시지 본문을 흉내낸 텍스트):
  "from: kim@corp.com amount: 42 category: meal desc: 팀 점심"
  "from: lee@corp.com amount: 780 category: travel desc: 부산 출장 KTX+호텔"
Gemini 키가 없으면 review_agent 가 규칙 기반 함수로 대체된다.
"""
import os
import re

from google.adk import Agent, Event, Workflow
from google.adk.events import RequestInput

MODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")
_KEY = os.getenv("GOOGLE_API_KEY", "")
USE_LLM = (bool(_KEY) and not _KEY.startswith("<")) or \
    os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE"


def parse_expense_email(node_input: str):
    def grab(key, default=""):
        m = re.search(rf"{key}:\s*(.+?)(?=\s+\w+:|$)", node_input)
        return m.group(1).strip() if m else default
    return {"sender": grab("from"), "amount": float(grab("amount", "0")),
            "category": grab("category", "etc"), "desc": grab("desc")}


def route_by_amount(node_input: dict):
    route = "AUTO_APPROVE" if node_input["amount"] < 100 else "NEEDS_REVIEW"
    return Event(output=node_input, route=route)


def auto_approve(node_input: dict):  # 쉬운 건은 모델 호출 없음 → 비용 0
    return Event(message=f"✅ 자동 승인: {node_input['sender']} ${node_input['amount']:.0f} ({node_input['category']})")


if USE_LLM:
    review_agent = Agent(
        name="review_agent", model=MODEL, mode="single_turn",
        instruction="입력된 경비 청구를 회사 정책(식대 1인 $50, 출장 숙박 1박 $200 상한) 관점에서 검토하고 "
                    "위험 요소와 권고(승인/보류)를 3줄 이내로 요약하라.")
else:
    def review_agent(node_input: dict):
        risk = "출장 상한 초과 가능성" if node_input["amount"] > 500 else "특이사항 없음"
        return f"검토 요약: {node_input['category']} ${node_input['amount']:.0f}, {risk}"


def request_approval(node_input: str):
    yield RequestInput(message=f"관리자 승인이 필요합니다.\n{node_input}\n승인하려면 yes, 아니면 no:",
                       payload={"review": node_input})


def process_decision(node_input):
    text = str(node_input.get("result", node_input) if isinstance(node_input, dict) else node_input)
    approved = text.strip().lower() in ("yes", "y", "승인", "true")
    return Event(message="✅ 관리자 승인 완료" if approved else "❌ 관리자 반려")


root_agent = Workflow(
    name="expense_processor",
    edges=[
        ("START", parse_expense_email, route_by_amount),
        (route_by_amount, {"AUTO_APPROVE": auto_approve,
                           "NEEDS_REVIEW": review_agent}),
        (review_agent, request_approval, process_decision),
    ])
