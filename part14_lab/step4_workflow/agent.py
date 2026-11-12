"""실습 4단계: Workflow 2.0 — 의도 분류 Route → 성적 / 수강신청 / 일반 문의.

START → guard_input → classify_intent ─ GRADE  → grade_lookup
                                        ├ ENROLL → enrollment_info
                                        ├ BLOCK  → blocked
                                        └ GENERAL→ general_answer (Agent, 키 없으면 템플릿)

규칙은 코드에(키워드 분류 = LLM 비용 0), 판단·문안만 LLM 에.
학번은 세션 State 의 user:student_id 에서 함수 노드 매개변수로 바인딩된다
(node_input 외 매개변수 이름은 ctx.state 에서 바인딩 — Part 9 슬라이드 100).
"""
import os
import re

from google.adk import Agent, Context, Event, Workflow
from step2_tools.agent import COURSES, ENROLLMENTS, GRADES
from step3_callback.guardrails import detect_pii

MODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")
_KEY = os.getenv("GOOGLE_API_KEY", "")
USE_LLM = (bool(_KEY) and not _KEY.startswith("<")) or \
    os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE"

INTENT_KEYWORDS = {
    "GRADE": ["성적", "학점 확인", "평점", "grade"],
    "ENROLL": ["수강신청", "수강 과목", "시간표", "신청", "수강중", "듣는 과목"],
}


def guard_input(node_input: str):
    found = detect_pii(node_input)
    return {"text": node_input, "pii": found}


def make_classifier(keywords: dict[str, list[str]]):
    """키워드 규칙으로 라우트를 고르는 함수 노드를 만든다 (앞에 있는 의도가 우선)."""
    def classify_intent(node_input: dict):
        if node_input["pii"]:
            return Event(output=node_input, route="BLOCK")
        text = node_input["text"]
        for intent, kws in keywords.items():
            if any(k in text for k in kws):
                return Event(output=node_input, route=intent)
        return Event(output=node_input, route="GENERAL")
    return classify_intent


def blocked(node_input: dict):
    return Event(message=f"개인정보({', '.join(node_input['pii'])})는 입력하지 마세요.")


def grade_lookup(ctx: Context, node_input: dict):
    sid = ctx.state.get("user:student_id")
    m = re.search(r"[A-Za-z]{2}\d{3}", node_input["text"])
    grades = GRADES.get(sid, {})
    if m:
        code = m.group(0).upper()
        g = grades.get(code)
        msg = f"{code} {COURSES.get(code, {}).get('title', '')} 성적: {g}" if g else f"{code} 성적이 없습니다."
    else:
        msg = "성적 목록: " + (", ".join(f"{c}({COURSES[c]['title']}) {g}" for c, g in grades.items()) or "없음")
    return Event(message=msg)


def enrollment_info(ctx: Context, node_input: dict):
    sid = ctx.state.get("user:student_id")
    codes = ENROLLMENTS.get(sid, [])
    total = sum(COURSES[c]["credits"] for c in codes)
    lines = ", ".join(f"{c} {COURSES[c]['title']}" for c in codes)
    return Event(message=f"이번 학기 수강 과목({total}학점): {lines}")


if USE_LLM:
    general_answer = Agent(
        name="general_answer", model=MODEL, mode="single_turn",
        instruction="너는 학사지원센터 상담원이다. 입력의 text 질문에 학사 일반 규정 관점에서 3문장 이내로 답하라. "
                    "모르면 학사지원센터(02-000-0000)를 안내하라.")
else:
    def general_answer(node_input: dict):
        return Event(message=f"[일반 문의 접수] '{node_input['text']}' — 학사지원센터(02-000-0000)로 안내드립니다.")


def build_edges(keywords: dict[str, list[str]] | None = None, extra_routes: dict | None = None):
    """5단계에서 의도·라우트를 추가해 재사용할 수 있도록 엣지를 함수로 만든다."""
    classify_intent = make_classifier(keywords or INTENT_KEYWORDS)
    routes = {"GRADE": grade_lookup, "ENROLL": enrollment_info,
              "BLOCK": blocked, "GENERAL": general_answer}
    routes.update(extra_routes or {})
    return [("START", guard_input, classify_intent), (classify_intent, routes)]


root_agent = Workflow(name="academic_workflow", edges=build_edges())
