"""실습 2단계: Function Tool — 수강 과목 조회 + ToolContext 로 State 저장.

학번은 사용자가 입력하지 않는다. 로그인 시 세션 State 의 user:student_id 로 주입된다
(3단계 가드레일에서 학번 입력 자체를 차단하기 때문).
"""
import os

from google.adk import Agent
from google.adk.tools import ToolContext

# ── 목업 학사 DB
COURSES = {
    "CS101": {"title": "프로그래밍기초", "credits": 3},
    "AI201": {"title": "에이전틱AI", "credits": 3},
    "MA110": {"title": "선형대수", "credits": 3},
    "EN100": {"title": "대학영어", "credits": 2},
}
ENROLLMENTS = {"S001": ["CS101", "AI201", "MA110"], "S002": ["AI201", "EN100"]}
GRADES = {"S001": {"CS101": "A+", "MA110": "B0"}, "S002": {"EN100": "A0"}}


def _student(tool_context: ToolContext) -> str | None:
    return tool_context.state.get("user:student_id")


def list_my_courses(tool_context: ToolContext) -> dict:
    """로그인한 학생의 이번 학기 수강 과목과 총 학점을 조회한다."""
    sid = _student(tool_context)
    if not sid:
        return {"status": "error", "error_message": "로그인 정보 없음"}
    codes = ENROLLMENTS.get(sid, [])
    courses = [{"code": c, **COURSES[c]} for c in codes]
    tool_context.state["last_courses"] = codes  # State 저장 → 이후 턴/노드에서 재사용
    return {"status": "success", "courses": courses, "total_credits": sum(c["credits"] for c in courses)}


def get_grade(course_code: str, tool_context: ToolContext) -> dict:
    """로그인한 학생의 과목 성적을 조회한다.

    Args:
        course_code: 과목 코드 (예: "CS101")
    """
    sid = _student(tool_context)
    if not sid:
        return {"status": "error", "error_message": "로그인 정보 없음"}
    grade = GRADES.get(sid, {}).get(course_code.upper())
    if grade is None:
        return {"status": "error", "error_message": f"{course_code} 성적 미입력 또는 미수강"}
    return {"status": "success", "course": course_code.upper(), "grade": grade}


def search_course(keyword: str) -> dict:
    """과목명 또는 코드로 개설 과목을 검색한다.

    Args:
        keyword: 검색어 (예: "AI", "선형")
    """
    hits = [{"code": c, **v} for c, v in COURSES.items() if keyword.lower() in (c + v["title"]).lower()]
    return {"status": "success", "results": hits}


root_agent = Agent(
    name="academic_tools",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    description="수강 과목·성적 조회가 가능한 학사 상담 에이전트",
    instruction="""
    너는 대학 학사지원센터 상담원이다. 로그인 학생: {user:name?}
    - 내 수강 과목/학점 → list_my_courses
    - 특정 과목 성적 → get_grade (과목명을 말하면 search_course 로 코드를 찾은 뒤)
    - 개설 과목 찾기 → search_course
    - 학번은 절대 묻지 않는다(로그인 정보로 자동 처리).
    도구 결과의 status 가 error 이면 error_message 를 쉬운 말로 설명한다.
    """,
    tools=[list_my_courses, get_grade, search_course],
)
