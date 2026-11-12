"""obs5 — OTLP로 span을 백엔드(Jaeger · Phoenix · Collector)에 보내기 (강의노트 Part 12 슬라이드 133 · 137). 📦

필요 패키지: uv pip install opentelemetry-exporter-otlp-proto-http   (또는 google-adk[otel])

실행: python obs5_otlp_export.py [--endpoint URL] [--selftest]
  --endpoint : OTLP/HTTP traces 주소 (기본 http://localhost:4318/v1/traces)
               Jaeger  : docker run --rm -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one
               Phoenix : 기본 http://localhost:6006/v1/traces
  --selftest : 백엔드 없이 확인. 이 스크립트가 4318 포트에 작은 수신기를 띄워 받은 요청을 센다.

adk web · adk api_server · agents-cli 서버는 OTEL_EXPORTER_OTLP_ENDPOINT 환경 변수만 있으면 같은 exporter를
스스로 등록한다(google.adk.telemetry.setup). Runner를 직접 쓰는 스크립트는 이 파일처럼 코드로 단다.
"""
import asyncio
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import _path  # noqa: F401
from _obs import install_telemetry, print_span_tree, run_turn, section, trace_ids, weather_agent

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
except ImportError:
    print("📦 opentelemetry-exporter-otlp-proto-http가 없습니다: uv pip install opentelemetry-exporter-otlp-proto-http")
    sys.exit(0)
from opentelemetry.sdk.trace.export import BatchSpanProcessor

ENDPOINT = sys.argv[sys.argv.index("--endpoint") + 1] if "--endpoint" in sys.argv else "http://localhost:4318/v1/traces"
RECEIVED: list[int] = []


class _Receiver(BaseHTTPRequestHandler):
    """--selftest용 가짜 OTLP 수신기: POST /v1/traces 본문(protobuf) 크기만 기록한다."""

    def do_POST(self):  # noqa: N802
        n = int(self.headers.get("Content-Length", 0))
        self.rfile.read(n)
        RECEIVED.append(n)
        self.send_response(200)
        self.send_header("Content-Type", "application/x-protobuf")
        self.end_headers()

    def log_message(self, *a):
        pass


def main():
    srv = None
    if "--selftest" in sys.argv:
        srv = ThreadingHTTPServer(("127.0.0.1", 4318), _Receiver)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    section(f"OTLP/HTTP → {ENDPOINT}" + ("  (selftest 수신기)" if srv else ""))
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=ENDPOINT))
    exporter, _ = install_telemetry(service_name="obs-lab", span_processors=[processor])
    asyncio.run(run_turn(weather_agent(), "서울 날씨 알려줘"))
    processor.force_flush()                          # 배치에 남은 span을 지금 보낸다
    spans = exporter.get_finished_spans()
    print_span_tree(spans)
    tid = next(iter(trace_ids(spans)))
    print(f"\n  보낸 span {len(spans)}개 · trace_id {tid}")
    if srv:
        print(f"  수신기가 받은 요청 {len(RECEIVED)}건 · {sum(RECEIVED)} bytes (protobuf)")
        srv.shutdown()
    else:
        print("  Jaeger: http://localhost:16686 에서 service=obs-lab 검색 · Phoenix: http://localhost:6006")


if __name__ == "__main__":
    main()
