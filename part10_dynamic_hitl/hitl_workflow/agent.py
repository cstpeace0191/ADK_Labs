"""강의노트 Part 10 슬라이드 105: Human-in-the-Loop — RequestInput (2-노드형, LLM 없음).

ask 가 RequestInput 을 yield 하면 실행이 일시정지되고,
사람이 응답을 보내면 그 값이 다음 노드(double)의 node_input 이 된다.
"""
from google.adk import Event, Workflow
from google.adk.events import RequestInput


def ask():  # 사람 입력 노드
    yield RequestInput(message="숫자를 입력하세요:")


def double(node_input):  # 응답이 node_input 으로
    try:
        return Event(message=f"{node_input} x 2 = {float(node_input) * 2:g}")
    except (TypeError, ValueError):
        return Event(message=f"숫자가 아닙니다: {node_input!r}")


root_agent = Workflow(name="hitl", edges=[("START", ask, double)])
