"""obs3 — ADK 내장 지표와 사용자 지표 (강의노트 Part 12 슬라이드 136). 🟢 LLM 없이 실행.

실행: python obs3_metrics.py [builtin|custom|all]
  builtin : 세 번의 요청 뒤 ADK가 기록한 지표(이름 · 종류 · 단위 · 차원)와 값 요약
  custom  : Plugin의 after_tool_callback에서 내 지표(도구 오류 수)를 직접 기록
"""
import asyncio
import sys

import _path  # noqa: F401
from _obs import install_telemetry, iter_metrics, run_turn, section, weather_agent
from opentelemetry import metrics
from opentelemetry.sdk.metrics.export import Histogram, Sum

_, READER = install_telemetry()

QUESTIONS = [
    ("서울 날씨 알려줘", [("get_weather", {"city": "Seoul"}), "서울은 맑고 21도입니다."]),
    ("부산은?", [("get_weather", {"city": "Busan"}), "부산은 흐리고 19도입니다."]),
    ("제주는?", [("get_weather", {"city": "Jeju"}), ("get_weather", {"city": "Jeju-si"}), "제주 날씨는 확인되지 않습니다."]),
]


def make_plugin():
    """도구 결과가 status=error면 lab.tool.errors 카운터를 1 올리는 Plugin."""
    from google.adk.plugins.base_plugin import BasePlugin

    meter = metrics.get_meter("obs_lab")
    tool_errors = meter.create_counter("lab.tool.errors", unit="1", description="오류를 돌려준 도구 호출 수")

    class ToolErrorMetricsPlugin(BasePlugin):
        async def after_tool_callback(self, *, tool, tool_args, tool_context, result):
            if isinstance(result, dict) and result.get("status") == "error":
                tool_errors.add(1, {"gen_ai.tool.name": tool.name, "gen_ai.agent.name": tool_context.agent_name})
            return None   # 결과는 바꾸지 않는다

    return ToolErrorMetricsPlugin(name="tool_error_metrics")


async def run_all(plugins=None):
    for q, script in QUESTIONS:
        await run_turn(weather_agent(script), q, plugins=plugins, show=False)


def _summary(m) -> list[str]:
    out = []
    for p in m.data.data_points:
        attrs = {k.replace("gen_ai.", ""): v for k, v in p.attributes.items()
                 if k in ("gen_ai.agent.name", "gen_ai.tool.name", "gen_ai.token.type", "gen_ai.request.model")}
        if isinstance(m.data, Histogram):
            out.append(f"      {attrs}  count={p.count} sum={round(p.sum, 4)}")
        elif isinstance(m.data, Sum):
            out.append(f"      {attrs}  value={p.value}")
    return out


DONE = False


def ensure_run():
    global DONE
    if not DONE:
        asyncio.run(run_all(plugins=[make_plugin()]))
        DONE = True


def builtin():
    section("builtin: 요청 3번 뒤 ADK가 기록한 지표 (meter: gcp.vertex.agent)")
    ensure_run()
    for scope, m in iter_metrics(READER.get_metrics_data()):
        if scope != "gcp.vertex.agent":
            continue
        kind = "Counter" if isinstance(m.data, Sum) else type(m.data).__name__
        print(f"  {m.name:<52} {kind:<9} {m.unit}")
        if m.name in ("gen_ai.invoke_agent.duration", "gen_ai.client.token.usage", "gen_ai.execute_tool.duration",
                      "gen_ai.invoke_agent.tool_calls"):
            print("\n".join(_summary(m)))
    print("\n  같은 지표를 속성(차원)으로 나눠 본다: 에이전트별 · 모델별 · 도구별 · 토큰 종류별")


def custom():
    section("custom: Plugin으로 기록한 내 지표 lab.tool.errors")
    ensure_run()
    found = False
    for scope, m in iter_metrics(READER.get_metrics_data()):
        if m.name == "lab.tool.errors":
            found = True
            print(f"  {m.name} (meter: {scope})")
            print("\n".join(_summary(m)))
    if not found:
        print("  (기록 없음)")
    print("\n  제주 질문에서 도구가 두 번 실패 → value=2. 이 값이 늘면 알림을 거는 것이 운영 지표의 출발점")


ITEMS = {"builtin": builtin, "custom": custom}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for k, fn in ITEMS.items():
        if which in (k, "all"):
            fn()
