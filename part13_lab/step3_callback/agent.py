"""실습 3단계: Callback — 학번·개인정보 입력 차단 가드레일 + 도구 인자 검증.

2단계 에이전트의 모델·지시문·도구를 그대로 쓰고 콜백만 추가한다.
"""
from google.adk import Agent
from step2_tools.agent import root_agent as step2

from .guardrails import block_pii, validate_course_code

root_agent = Agent(
    name="academic_guarded",
    model=step2.model,
    description=step2.description,
    instruction=step2.instruction,
    tools=list(step2.tools),
    before_model_callback=block_pii,
    before_tool_callback=validate_course_code,
)
