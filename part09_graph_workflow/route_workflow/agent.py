"""강의노트 Part 9 슬라이드 96: 코드 ② Route로 분기하기 (LLM 없음, 비용 0).

입력 "42"  → auto-approved $42
입력 "250" → needs review $250
"""
from google.adk import Event, Workflow


def parse(node_input: str):
    return {"amount": int(node_input)}


def route_by_amount(node_input: dict):
    route = "AUTO" if node_input["amount"] < 100 else "REVIEW"
    return Event(output=node_input, route=route)


def auto_approve(node_input: dict):
    return Event(message=f"auto-approved ${node_input['amount']}")


def review(node_input: dict):
    return Event(message=f"needs review ${node_input['amount']}")


root_agent = Workflow(name="routing", edges=[
    ("START", parse, route_by_amount),
    (route_by_amount, {"AUTO": auto_approve, "REVIEW": review}),
])
