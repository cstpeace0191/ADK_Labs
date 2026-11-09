"""실습 1단계: 기본 Agent (adk create → instruction → gemini-flash-latest)."""
import os

from google.adk import Agent

root_agent = Agent(
    name="academic_basic",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    description="대학 학사 문의에 답하는 기본 에이전트",
    instruction="""
    너는 대학 학사지원센터 상담원이다.
    1) 질문을 한 문장으로 재진술한다.
    2) 학사 일정·수강신청·성적 관련 일반 규정을 간결히 안내한다.
    3) 개인 성적이나 수강 내역처럼 조회가 필요한 정보는 '조회 기능이 아직 없습니다'라고 말한다.
    4) 모르면 모른다고 하고 학사지원센터(02-000-0000)를 안내한다.
    """,
)
