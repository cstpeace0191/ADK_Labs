"""강의노트 Part 7 슬라이드 80: State 접두사와 읽기·쓰기 방법.

접두사 | 범위
(없음) | 현재 세션            예: draft, visits
user:  | 같은 사용자의 모든 세션  예: user:name
app:   | 앱의 모든 사용자       예: app:notice
temp:  | 현재 호출(턴)만        예: temp:raw
"""
import os

from google.adk import Agent
from google.adk.tools import ToolContext


def remember_name(name: str, tool_context: ToolContext) -> dict:
    """사용자 이름을 기억한다(user 범위 → 같은 사용자의 다른 세션에서도 보인다).

    Args:
        name: 사용자 이름
    """
    tool_context.state["user:name"] = name
    return {"status": "success"}


def count_visit(tool_context: ToolContext) -> dict:
    """이번 세션의 방문 횟수를 1 늘리고, 턴 임시값(temp:)도 기록한다."""
    n = tool_context.state.get("visits", 0) + 1
    tool_context.state["visits"] = n                # 세션 범위
    tool_context.state["temp:last_tool"] = "count"  # 이번 턴만
    return {"status": "success", "visits": n, "notice": tool_context.state.get("app:notice")}


root_agent = Agent(
    name="state_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    instruction="""
    사용자 이름: {user:name?}
    공지: {app:notice?}
    - 사용자가 이름을 알려주면 remember_name 을 호출한다.
    - 매 요청마다 count_visit 를 한 번 호출하고 방문 횟수를 알려준다.
    - 공지가 있으면 첫 응답에 짧게 안내한다.
    """,
    tools=[remember_name, count_visit],
    output_key="last_reply",  # 쓰기 ①: 최종 응답을 state["last_reply"]에
)
