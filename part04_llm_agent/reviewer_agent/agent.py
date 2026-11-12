"""강의노트 Part 4 슬라이드 53: 구조화 출력 output_schema 와 output_key."""
import os

from google.adk import Agent
from pydantic import BaseModel, Field


class Review(BaseModel):
    score: int = Field(description="1~5점")
    summary: str
    risks: list[str]


root_agent = Agent(
    name="code_reviewer",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    description="코드 리뷰 결과를 JSON으로 반환한다.",
    instruction="입력 코드를 리뷰하고 JSON으로만 답하라.",
    output_schema=Review,  # 응답 형식 강제 (이 에이전트는 도구를 쓰지 않는다)
    output_key="review",   # state["review"]에 저장
)
