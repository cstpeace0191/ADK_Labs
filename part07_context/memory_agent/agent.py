"""강의노트 Part 7 슬라이드 87: Memory — preload_memory / load_memory.

preload_memory: 매 턴 자동으로 장기 기억을 검색해 프롬프트에 넣는다.
load_memory   : 모델이 필요할 때 도구로 검색한다.
"""
import os

from google.adk import Agent
from google.adk.tools import load_memory, preload_memory

root_agent = Agent(
    name="memory_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    instruction="사용자의 과거 대화에서 알게 된 사실(선호, 일정 등)을 활용해 답하라. "
                "기억에 없으면 load_memory 로 한 번 더 찾아보고, 그래도 없으면 모른다고 말하라.",
    tools=[preload_memory, load_memory],
)
