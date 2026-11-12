"""obs4 — 에이전트 지표를 OpenMetrics 형식으로 노출 (강의노트 Part 12 슬라이드 139). 🟢 LLM 없이 실행.

실행: python obs4_openmetrics.py [text|serve|prometheus|all]
  text       : ADK 지표를 OpenMetrics 텍스트로 바꿔 출력 (추가 패키지 없이 _obs.to_openmetrics 사용)
  serve      : http://127.0.0.1:9464/metrics 로 노출 → 브라우저나 curl로 '긁어 가기(scrape)'를 흉내 낸다
               (--seconds N: N초 뒤 종료, 기본은 Ctrl+C까지)
  prometheus : 공식 exporter(opentelemetry-exporter-prometheus)로 같은 일을 한다 📦
               설치: uv pip install opentelemetry-exporter-prometheus
'all'은 text만 실행한다 (serve · prometheus는 직접 고른다).
"""
import asyncio
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import _path  # noqa: F401
from _obs import install_telemetry, run_turn, section, to_openmetrics, weather_agent

MODE = sys.argv[1] if len(sys.argv) > 1 else "all"
PORT = 9464
CONTENT_TYPE = "application/openmetrics-text; version=1.0.0; charset=utf-8"

if MODE == "prometheus":
    try:
        from opentelemetry.exporter.prometheus import PrometheusMetricReader
    except ImportError:
        print("📦 opentelemetry-exporter-prometheus가 없습니다: uv pip install opentelemetry-exporter-prometheus")
        sys.exit(0)
    _, READER = install_telemetry(metric_reader=PrometheusMetricReader())
else:
    _, READER = install_telemetry()


async def traffic():
    await run_turn(weather_agent(), "서울 날씨 알려줘", show=False)
    await run_turn(weather_agent([("get_weather", {"city": "Busan"}), "부산은 흐림"]), "부산은?", show=False)


def text():
    section("text: ADK 지표 → OpenMetrics 텍스트 (일부: 토큰 · 에이전트 지연 · 도구 지연)")
    asyncio.run(traffic())
    body = to_openmetrics(READER.get_metrics_data())
    keep = ("gen_ai_client_inference_usage_input_tokens", "gen_ai_invoke_agent_duration_seconds",
            "gen_ai_execute_tool_duration_seconds", "# EOF")
    for line in body.splitlines():
        if any(k in line for k in keep):
            print("  " + line.replace(',otel_scope_name="gcp.vertex.agent"', ""))
    print("\n  규칙: 이름의 점(.) → 밑줄(_), 단위 s → _seconds, Counter → _total, 히스토그램 → _bucket/_count/_sum")
    print("  문서는 반드시 '# EOF'로 끝난다 — Prometheus 노출 형식과 OpenMetrics의 눈에 띄는 차이")


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path != "/metrics":
            self.send_error(404)
            return
        body = to_openmetrics(READER.get_metrics_data()).encode()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPE)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"  scrape ← {self.client_address[0]} {self.requestline}")


def _seconds() -> float | None:
    if "--seconds" in sys.argv:
        return float(sys.argv[sys.argv.index("--seconds") + 1])
    return None


def serve():
    section(f"serve: http://127.0.0.1:{PORT}/metrics")
    asyncio.run(traffic())
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"  curl http://127.0.0.1:{PORT}/metrics  또는 브라우저로 열어 보세요")
    print("  Prometheus라면 scrape_configs에 targets: ['127.0.0.1:9464'] 를 넣는다 (README 참고)")
    try:
        limit = _seconds()
        t0 = time.time()
        while limit is None or time.time() - t0 < limit:
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    srv.shutdown()


def prometheus():
    section(f"prometheus: 공식 exporter로 http://127.0.0.1:{PORT}/metrics 노출")
    from prometheus_client import start_http_server
    asyncio.run(traffic())
    start_http_server(PORT, addr="127.0.0.1")
    print(f"  curl -H 'Accept: application/openmetrics-text' http://127.0.0.1:{PORT}/metrics")
    try:
        limit = _seconds()
        t0 = time.time()
        while limit is None or time.time() - t0 < limit:
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass


ITEMS = {"text": text, "serve": serve, "prometheus": prometheus}

if __name__ == "__main__":
    if MODE == "all":
        text()
    else:
        ITEMS[MODE]()
