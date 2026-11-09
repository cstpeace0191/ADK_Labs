"""강의노트 Part 4 슬라이드 47: Instruction 설계와 State 템플릿 주입.

{course}     : 세션 State의 course 값 (없으면 오류 → 반드시 초기 State로 넣는다)
{user:name?} : user 범위 키, `?`가 붙어 있어 없으면 빈 값
"""
import os

from google.adk import Agent

root_agent = Agent(
    name="tutor",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    description="과목 조교 에이전트",
    instruction="""
    너는 {course} 과목 조교다.
    학생 이름: {user:name?}
    1) 먼저 질문을 한 문장으로 재진술한다.
    2) 개념 → 예시 → 확인 질문 순서로 답한다.
    3) 모르면 모른다고 말한다.
    학생 이름이 있으면 이름을 불러 존댓말로 답한다.
    """,
)
