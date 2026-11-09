"""강의노트 Part 9 슬라이드 98: 코드 ④ back-edge 루프 (생성 → 평가 → 수정, LLM 없음).

순환은 자동 제한이 없다 → 종료 조건(critic 의 DONE 라우트)이 필수.
"""
from google.adk import Event, Workflow


def seed(node_input):
    return {"n": 0}


def critic(node_input):
    return Event(
        route="DONE" if node_input["n"] >= 3 else "REVISE",
        output=node_input)


def refine(node_input):
    return {"n": node_input["n"] + 1}


def done(node_input):
    return f"finished after {node_input['n']} revisions"


root_agent = Workflow(name="loop_workflow", edges=[
    ("START", seed, critic),
    (critic, {"REVISE": refine, "DONE": done}),
    (refine, critic),  # back-edge
])
