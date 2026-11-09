"""강의노트 Part 10 슬라이드 103: Dynamic 병렬 실행(asyncio.gather) 과 parallel_worker (LLM 없음).

- research      : 주제 리스트를 받아 상한 5개까지 search_topic 을 병렬 실행
- followups     : 발견마다 후속 조사를 최대 3개, 깊이 2까지만 (모델 제안 + 코드 상한)
- review_case   : @node(parallel_worker=True) → 리스트 각 항목에 같은 작업, 입력 순서대로 결과 리스트
입력 예: "ADK, LangGraph, AutoGen"
"""
import asyncio

from google.adk import Context, Event, Workflow
from google.adk.workflow import node

MAX_TOPICS, MAX_FOLLOWUPS, MAX_DEPTH = 5, 3, 2


@node(name="search_topic")
async def search_topic(node_input: dict):
    await asyncio.sleep(0.05)  # 외부 검색 API 호출을 흉내
    topic, depth = node_input["topic"], node_input["depth"]
    # 가상의 '모델 제안': 더 조사할 하위 주제
    suggestions = [f"{topic}/sub{i}" for i in range(1, 6)] if depth < MAX_DEPTH else []
    return {"topic": topic, "depth": depth, "finding": f"{topic} 요약", "suggest": suggestions}


@node(rerun_on_resume=True)
async def research(ctx: Context, node_input: str):
    topics = [t.strip() for t in node_input.split(",") if t.strip()][:MAX_TOPICS]  # 상한 5개
    frontier = [{"topic": t, "depth": 1} for t in topics]
    findings = []
    while frontier:
        results = await asyncio.gather(*[ctx.run_node(search_topic, node_input=x) for x in frontier])
        findings.extend(results)
        # 모델이 '더 조사하자'고 해도 개수·깊이 상한은 코드가 정한다
        frontier = [{"topic": s, "depth": r["depth"] + 1}
                    for r in results for s in r["suggest"][:MAX_FOLLOWUPS]
                    if r["depth"] + 1 <= MAX_DEPTH]
    yield Event(message=f"조사 완료: {len(findings)}건 (주제 {len(topics)}개, 후속 ≤{MAX_FOLLOWUPS}, 깊이 ≤{MAX_DEPTH})")
    yield Event(output=[{"topic": f["topic"], "depth": f["depth"]} for f in findings])


@node(parallel_worker=True, max_parallel_workers=4)
def review_case(node_input: dict):
    return {"topic": node_input["topic"], "score": 10 - node_input["depth"] * 3}


def summarize(node_input: list):
    top = sorted(node_input, key=lambda x: -x["score"])[:3]
    return Event(message=f"점수 상위 3: {top}")


root_agent = Workflow(name="dynamic_parallel", edges=[
    ("START", research, review_case, summarize),
])
