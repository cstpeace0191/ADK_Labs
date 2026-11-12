"""강의노트 Part 4 슬라이드 55: Planner = 모델 thinking 설정 (계획 엔진이 아니다).

- BuiltInPlanner : 모델의 thinking 기능 설정 (thinking_level 또는 thinking_budget 중 하나만)
- PlanReActPlanner: /*PLANNING*/ /*ACTION*/ 태그 출력을 유도
"""
import os

from google.adk import Agent
from google.adk.planners import BuiltInPlanner, PlanReActPlanner
from google.genai import types

MODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")

thinking_agent = Agent(
    name="thinker",
    model=MODEL,
    instruction="단계적으로 생각한 뒤 결론만 간결히 답하라.",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_level="low",  # minimal | low | medium | high  (thinking_budget과 동시 사용 금지)
        )),
)

react_agent = Agent(
    name="reactor",
    model=MODEL,
    instruction="계획을 세우고 답하라.",
    planner=PlanReActPlanner(),
)

# adk web 에서는 thinker 를 기본으로 노출
root_agent = thinking_agent
