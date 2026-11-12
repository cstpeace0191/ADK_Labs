"""실습 5단계: HITL + Retry — 수강 취소는 RequestInput 승인, 외부 학사 API 에 RetryConfig.

4단계 그래프에 DROP 라우트를 추가한다:
classify_intent ─ DROP → fetch_registrar(Retry) → confirm_drop(RequestInput) ─ CONFIRM → apply_drop
                                                                              └ CANCEL  → drop_cancelled
되돌리기 어려운 쓰기(apply_drop)는 사람 승인 '이후' 노드에 두어, 재시도·재개 시 중복 실행을 막는다.
"""
import random

from google.adk import Context, Event, Workflow
from google.adk.events import RequestInput
from google.adk.workflow import RetryConfig, node
from pydantic import BaseModel
from step2_tools.agent import COURSES, ENROLLMENTS
from step4_workflow import agent as step4

FLAKY_RATE = 0.5  # 외부 API 일시 오류 확률 (실습용)
_rng = random.Random(7)


class RegistrarUnavailable(ConnectionError):
    pass


def _call_registrar(student_id: str, code: str) -> dict:
    if _rng.random() < FLAKY_RATE:
        raise RegistrarUnavailable("학사 API 일시 장애")
    enrolled = code in ENROLLMENTS.get(student_id, [])
    return {"code": code, "title": COURSES.get(code, {}).get("title", "?"), "enrolled": enrolled,
            "refund_rate": "100%" if enrolled else "-", "deadline": "2026-11-20"}


@node(retry_config=RetryConfig(max_attempts=5, initial_delay=0.2, jitter=0,
                               exceptions=[RegistrarUnavailable]),
      timeout=5.0)
def fetch_registrar(ctx: Context, node_input: dict):
    import re
    sid = ctx.state.get("user:student_id")
    m = re.search(r"[A-Za-z]{2}\d{3}", node_input["text"])
    if not m:
        return {"error": "취소할 과목 코드를 함께 입력하세요 (예: MA110 수강 취소)"}
    return _call_registrar(sid, m.group(0).upper())


class DropDecision(BaseModel):
    confirm: bool
    reason: str = ""


@node(rerun_on_resume=True)
async def confirm_drop(ctx: Context, node_input: dict):
    if node_input.get("error") or not node_input.get("enrolled"):
        yield Event(output={**node_input, "reason": node_input.get("error", "수강 중인 과목이 아님")},
                    route="CANCEL")
        return
    answer = ctx.resume_inputs.get("drop_confirm")
    if answer is None:
        yield RequestInput(interrupt_id="drop_confirm",
                           message=f"{node_input['code']} {node_input['title']} 수강을 취소할까요? "
                                   f"(마감 {node_input['deadline']}, 환불 {node_input['refund_rate']})",
                           payload=node_input, response_schema=DropDecision)
        return
    d = DropDecision.model_validate(answer)
    yield Event(output={**node_input, "reason": d.reason}, route="CONFIRM" if d.confirm else "CANCEL")


def apply_drop(ctx: Context, node_input: dict):
    sid = ctx.state.get("user:student_id")
    ENROLLMENTS[sid] = [c for c in ENROLLMENTS.get(sid, []) if c != node_input["code"]]  # 목업 DB 쓰기
    ctx.state["drop_log"] = ctx.state.get("drop_log", []) + [node_input["code"]]
    return Event(message=f"✅ {node_input['code']} {node_input['title']} 수강 취소 완료. "
                         f"남은 과목: {', '.join(ENROLLMENTS[sid]) or '없음'}")


def drop_cancelled(node_input: dict):
    return Event(message=f"수강 취소를 진행하지 않았습니다. ({node_input.get('reason') or '사용자 취소'})")


# DROP 이 ENROLL('수강 과목' 등)보다 먼저 검사되도록 맨 앞에 둔다
KEYWORDS = {"DROP": ["수강 취소", "수강취소", "드랍", "drop"], **step4.INTENT_KEYWORDS}

root_agent = Workflow(name="academic_hitl", edges=step4.build_edges(KEYWORDS, {"DROP": fetch_registrar}) + [
    (fetch_registrar, confirm_drop),
    (confirm_drop, {"CONFIRM": apply_drop, "CANCEL": drop_cancelled}),
])
