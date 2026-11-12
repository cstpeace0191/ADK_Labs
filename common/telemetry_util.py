"""OpenTelemetry 실습 공통 도구 (Part 12 관측성 · Part 14 실습 7단계에서 사용, LLM 불필요).

- install_telemetry(): ADK보다 먼저 TracerProvider · MeterProvider를 등록한다.
  ADK는 이미 등록된 provider를 덮어쓰지 않으므로, 여기서 고른 exporter로 신호가 나간다.
- print_span_tree(): 끝난 span을 부모-자식 트리 + 막대(waterfall)로 출력 (adk web Trace 탭과 같은 모양)
- fake_llm(): 대본대로 답하는 가짜 모델(BaseLlm 상속) — LLM 없이도 generate_content span · 토큰 지표가 생긴다
- iter_metrics() · to_openmetrics(): OTel 지표를 순회하고 OpenMetrics 텍스트로 바꾼다 (추가 패키지 없이)
"""
from __future__ import annotations

import math
import re
from typing import AsyncGenerator, Iterable

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import Histogram, InMemoryMetricReader, MetricsData, Sum
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


# --------------------------------------------------------------------------- 텔레메트리 설치
def install_telemetry(service_name: str = "obs-lab", metric_reader=None, span_processors=()):
    """메모리 exporter(+추가 processor)를 단 TracerProvider와 MeterProvider를 전역으로 등록한다.

    반드시 Runner를 실행하기 전에 호출한다. 돌려주는 값: (span_exporter, metric_reader)
    """
    resource = Resource.create({"service.name": service_name})
    exporter = InMemorySpanExporter()
    tp = TracerProvider(resource=resource)
    tp.add_span_processor(SimpleSpanProcessor(exporter))
    for p in span_processors:
        tp.add_span_processor(p)
    trace.set_tracer_provider(tp)
    reader = metric_reader or InMemoryMetricReader()
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))
    return exporter, reader


# --------------------------------------------------------------------------- span 출력
def _depth(span: ReadableSpan, by_id: dict) -> int:
    d = 0
    while span.parent is not None and span.parent.span_id in by_id:
        span = by_id[span.parent.span_id]
        d += 1
    return d


def print_span_tree(spans: Iterable[ReadableSpan], *, attrs: bool | list[str] = False, width: int = 72) -> None:
    """span을 트리 + 막대(waterfall)로 출력한다. attrs=True면 모든 속성, 목록이면 그 접두사만."""
    spans = list(spans)
    if not spans:
        print("  (span 없음)")
        return
    by_id = {s.context.span_id: s for s in spans}
    spans.sort(key=lambda s: (s.start_time, _depth(s, by_id)))
    t0 = min(s.start_time for s in spans)
    t1 = max(s.end_time for s in spans)
    total = max(t1 - t0, 1)
    bar_w = 24
    for s in spans:
        d = _depth(s, by_id)
        a = int((s.start_time - t0) / total * bar_w)
        b = max(a + 1, int((s.end_time - t0) / total * bar_w))
        bar = " " * a + "█" * (b - a) + " " * (bar_w - b)
        name = ("  " * d + s.name)[:40]
        print(f"  {name:<40} |{bar}| {(s.end_time - s.start_time) / 1e6:7.1f} ms")
        if attrs:
            for k, v in s.attributes.items():
                if attrs is True or any(k.startswith(p) for p in attrs):
                    print(f"  {'  ' * d}    {k} = {str(v)[:width]}")


def trace_ids(spans: Iterable[ReadableSpan]) -> set[str]:
    return {format(s.context.trace_id, "032x") for s in spans}


# --------------------------------------------------------------------------- 지표
def iter_metrics(data: MetricsData | None):
    if data is None:
        return
    for rm in data.resource_metrics:
        for sm in rm.scope_metrics:
            for m in sm.metrics:
                yield sm.scope.name, m


_INVALID = re.compile(r"[^a-zA-Z0-9_:]")


def _om_name(name: str, unit: str, kind: str) -> str:
    """OTel → Prometheus/OpenMetrics 이름 규칙(요약): 점 → 밑줄, 단위 s → _seconds, Counter → _total."""
    n = _INVALID.sub("_", name)
    if unit == "s" and not n.endswith("_seconds"):
        n += "_seconds"
    if kind == "counter":
        n += "_total"
    return n


def _om_labels(attrs: dict, extra: dict | None = None) -> str:
    items = {**{_INVALID.sub("_", k): v for k, v in attrs.items()}, **(extra or {})}
    if not items:
        return ""
    body = ",".join(f'{k}="{str(v).replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}"'
                    for k, v in sorted(items.items()))
    return "{" + body + "}"


def _num(x: float) -> str:
    f = float(x)
    if f == math.inf:
        return "+Inf"
    return str(int(f)) if f.is_integer() else repr(f)


def to_openmetrics(data: MetricsData | None, only_prefix: str = "") -> str:
    """OTel MetricsData를 OpenMetrics 텍스트로 바꾼다 (counter와 histogram만, 실습용 축약판)."""
    lines: list[str] = []
    for _scope, m in iter_metrics(data):
        if only_prefix and not m.name.startswith(only_prefix):
            continue
        if isinstance(m.data, Sum) and m.data.is_monotonic:
            family = _om_name(m.name, m.unit, "counter")[: -len("_total")]
            lines += [f"# TYPE {family} counter", f"# UNIT {family} {m.unit}" if m.unit == "s" else None,
                      f"# HELP {family} {m.description}"]
            for p in m.data.data_points:
                lines.append(f"{family}_total{_om_labels(dict(p.attributes))} {_num(p.value)}")
        elif isinstance(m.data, Histogram):
            family = _om_name(m.name, m.unit, "histogram")
            lines += [f"# TYPE {family} histogram", f"# UNIT {family} seconds" if m.unit == "s" else None,
                      f"# HELP {family} {m.description}"]
            for p in m.data.data_points:
                attrs = dict(p.attributes)
                cum = 0
                for bound, cnt in zip(list(p.explicit_bounds) + [math.inf], p.bucket_counts):
                    cum += cnt
                    if cnt or bound == math.inf:   # 실습 출력이 길어지지 않게 빈 버킷은 생략
                        lines.append(f"{family}_bucket{_om_labels(attrs, {'le': _num(bound)})} {cum}")
                lines.append(f"{family}_count{_om_labels(attrs)} {p.count}")
                lines.append(f"{family}_sum{_om_labels(attrs)} {_num(round(p.sum, 6))}")
    lines.append("# EOF")
    return "\n".join(x for x in lines if x is not None) + "\n"


# --------------------------------------------------------------------------- 가짜 모델
def _make_fake_llm_class():
    from google.adk.models import BaseLlm, LlmResponse
    from google.genai import types

    class FakeLlm(BaseLlm):
        """script 원소: str → 텍스트 답, (name, args) → 도구 호출. 호출마다 usage_metadata를 붙인다."""

        script: list = []
        prompt_tokens: int = 120
        output_tokens: int = 15
        calls: int = 0

        async def generate_content_async(self, llm_request, stream: bool = False) -> AsyncGenerator:
            step = self.script[self.calls] if self.calls < len(self.script) else "(대본 끝)"
            self.calls += 1
            if isinstance(step, tuple):
                part = types.Part(function_call=types.FunctionCall(name=step[0], args=step[1]))
            else:
                part = types.Part(text=step)
            usage = types.GenerateContentResponseUsageMetadata(
                prompt_token_count=self.prompt_tokens, candidates_token_count=self.output_tokens,
                total_token_count=self.prompt_tokens + self.output_tokens)
            yield LlmResponse(content=types.Content(role="model", parts=[part]), usage_metadata=usage)

    return FakeLlm


def fake_llm(script: list, model: str = "fake-gemini", **kw):
    return _make_fake_llm_class()(model=model, script=list(script), **kw)
