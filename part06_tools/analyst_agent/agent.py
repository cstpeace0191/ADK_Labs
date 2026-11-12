"""강의노트 Part 6 슬라이드 79: 내장 도구와 AgentTool — 검색/코드실행 에이전트를 도구로 감싸기.

google_search · BuiltInCodeExecutor 는 Gemini 전용 내장 도구라 다른 도구와 한 에이전트에
섞기 어렵다 → 각각 전담 에이전트로 만들고 AgentTool로 감싸 부모가 함수처럼 호출한다.
"""
import os

from google.adk import Agent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

# adk web/run 은 part06_tools 폴더를 sys.path에 넣으므로 형제 에이전트 패키지를 그대로 import 한다
from shop_agent.agent import add_to_cart, list_products

MODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")

search_agent = Agent(
    name="searcher",
    model=MODEL,
    description="웹 검색으로 사실을 찾아 출처와 함께 요약한다.",
    instruction="웹 검색으로 사실을 찾아 출처와 함께 요약하라.",
    tools=[google_search],
)

coder = Agent(
    name="calculator",
    model=MODEL,
    description="파이썬 코드를 실행해 정확한 계산 결과를 낸다.",
    instruction="계산은 반드시 코드를 작성·실행해서 답하라.",
    code_executor=BuiltInCodeExecutor(),
)

root_agent = Agent(
    name="analyst",
    model=MODEL,
    instruction="사실은 searcher, 계산은 calculator로 처리하라. "
                "상품 담기 요청은 list_products/add_to_cart를 쓴다.",
    tools=[AgentTool(agent=search_agent), AgentTool(agent=coder),
           list_products, add_to_cart],
)
