"""강의노트 Part 4 슬라이드 54: 모델 선택 — Gemini 기본, LiteLLM 경유로 다른 공급자.

ANTHROPIC_API_KEY 가 있으면 Claude 모델을, 없으면 Gemini 로 대체한다.
"""
import os

from google.adk import Agent

if os.getenv("ANTHROPIC_API_KEY"):
    from google.adk.models.lite_llm import LiteLlm

    model = LiteLlm(model=os.getenv("LITELLM_MODEL", "anthropic/claude-sonnet-5-5"))
else:
    model = os.getenv("ADK_MODEL", "gemini-flash-latest")

root_agent = Agent(
    name="multi_model_agent",
    model=model,
    instruction="너는 어떤 모델 위에서 동작하는지 한 문장으로 소개하고 질문에 답하라.",
)
