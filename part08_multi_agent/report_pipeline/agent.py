"""강의노트 Part 8 슬라이드 88: 1.x Workflow Agent — Sequential · Parallel · Loop.

값 전달: 각 에이전트의 output_key → 다음 instruction 의 {key}
(1.x 코드를 읽을 줄 알아야 하지만, 새 코드는 Part 9 Graph Workflow(실습 part09)로 작성한다)
"""
import os

from google.adk import Agent
from google.adk.agents import LoopAgent, ParallelAgent, SequentialAgent
from google.adk.tools import ToolContext

MODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")

news_agent = Agent(
    name="news_agent", model=MODEL,
    instruction="사용자가 준 주제에 대해 최근 업계 동향 3가지를 불릿으로 써라(가상 예시 허용).",
    output_key="news")

paper_agent = Agent(
    name="paper_agent", model=MODEL,
    instruction="사용자가 준 주제에 대해 대표 연구 방향 3가지를 불릿으로 써라.",
    output_key="papers")

research = ParallelAgent(name="research", sub_agents=[news_agent, paper_agent])  # 동시에

draft_agent = Agent(
    name="draft_agent", model=MODEL,
    instruction="다음 자료로 5문장 보고서 초안을 써라.\n동향:\n{news}\n연구:\n{papers}",
    output_key="draft")


def exit_loop(tool_context: ToolContext) -> dict:
    """초안이 충분히 좋으면 호출해 개선 루프를 끝낸다."""
    tool_context.actions.escalate = True
    return {"status": "approved"}


critic_agent = Agent(
    name="critic_agent", model=MODEL,
    instruction="초안:\n{draft}\n\n문장이 5개이고 동향과 연구가 모두 반영되었으면 exit_loop 를 호출하라. "
                "아니면 고칠 점을 한 문장으로 써라.",
    tools=[exit_loop],
    output_key="critique")

writer_agent = Agent(
    name="writer_agent", model=MODEL,
    instruction="초안:\n{draft}\n지적:\n{critique?}\n지적을 반영해 초안 전체를 다시 써라.",
    output_key="draft")

refine = LoopAgent(name="refine", max_iterations=3,
                   sub_agents=[critic_agent, writer_agent])  # 반복

root_agent = SequentialAgent(name="report_pipeline",
                             sub_agents=[research, draft_agent, refine])  # 순서대로
