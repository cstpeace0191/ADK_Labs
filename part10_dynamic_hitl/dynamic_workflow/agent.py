"""강의노트 Part 10 슬라이드 102: Dynamic Workflow — 엣지 대신 파이썬 제어 흐름 (LLM 없음).

ctx.run_node(child, node_input=...) 로 자식 노드를 코드에서 스케줄한다.
run_node 를 부르는 부모 노드는 rerun_on_resume=True 가 필수.
출력: sum of squares=14
"""
from google.adk import Context, Event, Workflow
from google.adk.workflow import node


@node(name="square")
def square(node_input: int):
    return node_input * node_input


@node(rerun_on_resume=True)  # run_node를 부르는 부모는 필수
async def orchestrate(ctx: Context, node_input: str):
    total = 0
    for i in range(1, 4):  # 평범한 for 루프
        total += await ctx.run_node(square, node_input=i)
    yield Event(message=f"sum of squares={total}")


root_agent = Workflow(name="dynamic", edges=[("START", orchestrate)])
