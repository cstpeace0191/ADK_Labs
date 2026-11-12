"""obs1 — ADK가 만드는 span 트리와 GenAI 속성 (강의노트 Part 12 슬라이드 133–135). 🟢 LLM 없이 실행.

실행: python obs1_span_tree.py [tree|attrs|legacy|all]
  tree   : 한 턴(모델 → 도구 → 모델)의 span 트리와 막대 그래프
  attrs  : 각 span의 gen_ai.* 속성 (OpenTelemetry GenAI 의미 규약)
  legacy : ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN=1(레거시 형식)과 span 이름 비교
"""
import asyncio
import os
import subprocess
import sys

import _path  # noqa: F401
from _obs import install_telemetry, print_span_tree, run_turn, section, trace_ids, weather_agent

SPAN_EXPORTER, _ = install_telemetry()   # ← ADK를 실행하기 전에 provider부터 등록


async def one_turn():
    SPAN_EXPORTER.clear()
    await run_turn(weather_agent(), "서울 날씨 알려줘")
    return SPAN_EXPORTER.get_finished_spans()


def tree():
    section("tree: 한 턴의 span 트리 (google-adk 기본 형식 = 스키마 v2)")
    spans = asyncio.run(one_turn())
    print_span_tree(spans)
    print(f"\n  span {len(spans)}개 · trace_id {len(trace_ids(spans))}개 → 한 요청 = trace 하나")
    print("  span 이름 = '{gen_ai.operation.name} {대상}' — invoke_workflow > invoke_agent > generate_content / execute_tool")


def attrs():
    section("attrs: span 속성 (gen_ai.* = GenAI 의미 규약, gcp.vertex.agent.* = ADK 이벤트 연결용)")
    spans = asyncio.run(one_turn())
    print_span_tree(spans, attrs=["gen_ai.", "gcp.vertex.agent."], width=60)
    llm = [s for s in spans if s.name.startswith("generate_content")]
    inp = sum(s.attributes.get("gen_ai.usage.input_tokens", 0) for s in llm)
    out = sum(s.attributes.get("gen_ai.usage.output_tokens", 0) for s in llm)
    print(f"\n  모델 호출 {len(llm)}번 · 입력 토큰 합 {inp} · 출력 토큰 합 {out}  ← 비용 계산의 출발점")
    has_content = any(k in s.attributes for s in spans for k in ("gen_ai.input.messages", "gen_ai.tool.call.arguments"))
    print(f"  프롬프트·도구 인자 같은 '내용' 속성이 있는가? {has_content}  (기본은 기록 안 함 → obs2)")


def legacy():
    section("legacy: 스키마 v1(레거시)과 v2(기본) span 이름 비교")
    if os.getenv("_OBS_CHILD"):
        spans = asyncio.run(one_turn())
        print_span_tree(spans)
        return
    for ver in ("2", "1"):
        print(f"\n  ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN={ver}")
        env = {**os.environ, "ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN": ver, "_OBS_CHILD": "1", "PYTHONIOENCODING": "utf-8"}
        out = subprocess.run([sys.executable, __file__, "legacy"], env=env, capture_output=True, text=True,
                             encoding="utf-8").stdout
        print("\n".join(line for line in out.splitlines() if "|" in line))
    print("\n  v1: invocation > invoke_agent > call_llm > generate_content (2.6.3 등 이전 버전과 같은 모양)")
    print("  v2: invoke_workflow > invoke_agent > generate_content — OTel GenAI 규약에 맞춰 call_llm이 빠졌다")


ITEMS = {"tree": tree, "attrs": attrs, "legacy": legacy}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for k, fn in ITEMS.items():
        if which in (k, "all"):
            fn()
