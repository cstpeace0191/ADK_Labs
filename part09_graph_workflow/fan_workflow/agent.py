"""강의노트 Part 9 슬라이드 97: 코드 ③ Fan-out 과 JoinNode Fan-in (LLM 없음).

("START", (a, b), join) : a, b 를 병렬 실행 → JoinNode 가 {노드이름: 결과} dict 로 합친다.
"""
from google.adk import Event, Workflow
from google.adk.workflow import JoinNode


def a(node_input):
    return "A"


def b(node_input):
    return "B"


join = JoinNode(name="join")


def final(node_input):
    return Event(message=f"joined={node_input}")


root_agent = Workflow(name="fan", edges=[
    ("START", (a, b), join),
    (join, final),
])
