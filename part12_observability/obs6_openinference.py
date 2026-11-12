"""obs6 — OpenInference 계측과 Phoenix (강의노트 Part 12 슬라이드 140). 📦

필요 패키지: uv pip install openinference-instrumentation-google-adk arize-phoenix-otel
Phoenix UI : uv pip install arize-phoenix 후 'phoenix serve' (또는 docker run -p 6006:6006 arizephoenix/phoenix)

실행: python obs6_openinference.py [local|phoenix|hide|all]
  local   : 메모리 exporter로 OpenInference span(이름 · span.kind · llm.* 속성)을 출력  (Phoenix 없이)
  phoenix : phoenix.otel.register()로 실행 중인 Phoenix(http://localhost:6006)에 보낸다
  hide    : OPENINFERENCE_HIDE_INPUTS/OUTPUTS로 내용을 숨겼을 때와 비교 (OpenInference는 기본으로 내용을 기록한다)
'all'은 local과 hide만 실행한다.
"""
import asyncio
import json
import os
import subprocess
import sys

import _path  # noqa: F401
from _obs import print_span_tree, run_turn, section, weather_agent

try:
    from openinference.instrumentation.google_adk import GoogleADKInstrumentor
except ImportError:
    print("📦 openinference-instrumentation-google-adk가 없습니다:")
    print("   uv pip install openinference-instrumentation-google-adk arize-phoenix-otel")
    sys.exit(0)

OI_KEYS = ("openinference.span.kind", "llm.model_name", "llm.token_count.", "tool.name", "session.id",
           "agent.name", "input.value", "output.value")
PII = "20261234"
QUESTION = f"제 학번은 {PII}이에요. 서울 날씨 알려줘"


def local():
    section("local: OpenInference 계측을 켠 ADK 실행 (span 이름과 속성이 바뀐다)")
    from _obs import install_telemetry
    exporter, _ = install_telemetry()
    from opentelemetry import trace
    GoogleADKInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
    asyncio.run(run_turn(weather_agent(), "서울 날씨 알려줘"))
    spans = exporter.get_finished_spans()
    print_span_tree(spans, attrs=list(OI_KEYS), width=50)
    kinds = sorted({s.attributes.get("openinference.span.kind", "-") for s in spans})
    print(f"\n  span.kind: {kinds} — CHAIN(invocation) > AGENT > LLM · TOOL")
    print("  ADK 기본(gen_ai.usage.input_tokens) ↔ OpenInference(llm.token_count.prompt) — 같은 값, 다른 이름")
    GoogleADKInstrumentor().uninstrument()


def _child_hide():
    from _obs import install_telemetry
    exporter, _ = install_telemetry()
    from opentelemetry import trace
    GoogleADKInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
    asyncio.run(run_turn(weather_agent(), QUESTION, show=False))
    spans = exporter.get_finished_spans()
    leak = sorted({s.name for s in spans if any(PII in str(v) for v in s.attributes.values())})
    print(json.dumps({"leak": leak}, ensure_ascii=False))


def hide():
    section(f"hide: 학번({PII})이 OpenInference span에 남는가?")
    for label, extra in [("기본", {}), ("HIDE_INPUTS·OUTPUTS·MESSAGES=true",
                                        {"OPENINFERENCE_HIDE_INPUTS": "true", "OPENINFERENCE_HIDE_OUTPUTS": "true",
                                         "OPENINFERENCE_HIDE_INPUT_MESSAGES": "true",
                                         "OPENINFERENCE_HIDE_OUTPUT_MESSAGES": "true"})]:
        env = {**os.environ, "_OBS_CHILD": "1", "PYTHONIOENCODING": "utf-8", **extra}
        out = subprocess.run([sys.executable, __file__], env=env, capture_output=True, text=True, encoding="utf-8")
        line = [ln for ln in out.stdout.splitlines() if ln.startswith("{")]
        leak = json.loads(line[-1])["leak"] if line else ["(실행 실패)"]
        print(f"  {label:<34} → {'유출 ✗ ' + ', '.join(leak) if leak else '안전 ✓'}")
    print("\n  ADK 기본 계측은 기본이 '내용 없음', OpenInference는 기본이 '내용 기록' — 운영 전에 반드시 확인")


def phoenix():
    section("phoenix: Phoenix로 보내기 (phoenix serve가 실행 중이어야 한다)")
    from phoenix.otel import register
    tp = register(project_name="adk-obs-lab", endpoint=os.getenv("PHOENIX_COLLECTOR_ENDPOINT",
                                                                  "http://localhost:6006/v1/traces"))
    GoogleADKInstrumentor().instrument(tracer_provider=tp)
    asyncio.run(run_turn(weather_agent(), "서울 날씨 알려줘"))
    tp.force_flush()
    print("  http://localhost:6006 → 프로젝트 adk-obs-lab → Traces 탭에서 AGENT > LLM · TOOL 트리 확인")


ITEMS = {"local": local, "hide": hide, "phoenix": phoenix}

if __name__ == "__main__":
    if os.getenv("_OBS_CHILD"):
        _child_hide()
        sys.exit(0)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which == "all":
        local()
        hide()
    else:
        ITEMS[which]()
