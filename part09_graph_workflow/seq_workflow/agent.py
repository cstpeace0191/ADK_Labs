"""강의노트 Part 9 슬라이드 100: 코드 ① 순차 워크플로우와 데이터 전달 (Agent 노드 → LLM 필요).

데이터 흐름 규칙
- 반환값 → 다음 노드의 node_input
- node_input 외의 매개변수 이름은 기본적으로 ctx.state 에서 바인딩
- Pydantic 모델로 노드 간 계약을 고정
"""
import os

from google.adk import Agent, Event, Workflow
from pydantic import BaseModel

MODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")

city_generator = Agent(
    name="city_generator", model=MODEL,
    instruction="임의의 도시 이름 하나만 출력하라. 다른 말은 하지 마라.")


class CityTime(BaseModel):
    time_info: str
    city: str


def lookup_time(node_input: str):  # 함수 노드
    return CityTime(time_info="10:10 AM", city=node_input.strip())


city_report = Agent(
    name="city_report", model=MODEL,
    input_schema=CityTime,  # 구조화 입력: 앞 노드의 CityTime 이 JSON 으로 전달된다
    # 주의: {CityTime.time_info} 처럼 쓰면 State 템플릿이 아니라 글자 그대로 모델에 간다.
    #       입력 JSON 의 필드를 쓰라고 지시한다.
    instruction="입력 JSON의 time_info 와 city 로 'It is <time_info> in <city>.' 한 문장만 답하라.")


def done(node_input: str):
    return Event(message=f"{node_input}\n WORKFLOW COMPLETED.")


root_agent = Workflow(name="seq_workflow", edges=[
    ("START", city_generator, lookup_time, city_report, done)])
