# part12_observability — Part 12. Observability(관측성)

> 강의노트 **Part 12 · 12. Observability(관측성)** (슬라이드 130–142)와 짝을 이룬다.
> 에이전트가 **왜** 그렇게 행동했는지를 Trace · Metrics · Logs로 거슬러 확인한다.
> OpenTelemetry(ADK 내장) · OpenMetrics(지표 노출 형식) · OpenInference(AI 전용 Trace 규약)를 직접 실행해 비교한다.

**obs1–obs4는 🟢 LLM 없이 실행된다** (Gemini 키 불필요). 실습용 가짜 모델(`_obs.FakeLlm`)이 `BaseLlm`을 상속해
실제 모델 자리에 들어가므로, ADK가 만드는 `generate_content` span과 토큰 지표가 Gemini를 쓸 때와 똑같이 생긴다.
(부록 A의 `before_model_callback` 방식은 모델 호출 자체를 건너뛰어 이런 span이 생기지 않는다.)

## 실행

`ADK_Labs/part12_observability` 폴더에서:

```bash
uv run run_all.py --quiet                 # 오프라인 실습 전체를 실행하고 요약만 보기
uv run obs1_span_tree.py tree             # 항목 하나만 실행 (항목 없이 실행하면 all)
```

선택 실습(📦)은 패키지를 따로 설치한다. 실습 환경(`uv.lock`)은 바꾸지 않으므로 필요한 사람만 설치한다.

```bash
uv pip install opentelemetry-exporter-otlp-proto-http        # obs5 (google-adk[otel]에도 들어 있다)
uv pip install opentelemetry-exporter-prometheus             # obs4 prometheus
uv pip install openinference-instrumentation-google-adk arize-phoenix-otel   # obs6
```

## 슬라이드 ↔ 실습 지도

| 슬라이드 | 스크립트 · 항목 | 확인할 것 |
|---|---|---|
| 133 OpenTelemetry 구조 | `obs1_span_tree.py tree` · `obs5_otlp_export.py` | provider를 먼저 등록하면 ADK는 덮어쓰지 않는다 · exporter만 바꿔 보낼 곳을 고른다 |
| 134 ADK span 트리 | `obs1_span_tree.py tree` · `legacy` | `invoke_workflow > invoke_agent > generate_content · execute_tool` / 레거시(v1)는 `invocation > … > call_llm` |
| 135 GenAI 속성 | `obs1_span_tree.py attrs` | `gen_ai.usage.input_tokens` · `gen_ai.tool.name` · `gen_ai.conversation.id` … |
| 136 ADK 내장 지표 | `obs3_metrics.py builtin` · `custom` | 지표 이름 · 종류 · 차원 / Plugin으로 내 지표(`lab.tool.errors`) 추가 |
| 137 관측 켜기 | `obs_agent/` (🔑) · `obs5_otlp_export.py` (📦) | `adk web` Trace 탭 · `OTEL_EXPORTER_OTLP_ENDPOINT` · `--otel_to_cloud` |
| 138 내용 기록 · 개인정보 | `obs2_content_capture.py modes` · `pii` | 기본은 내용 없음 · `SPAN_ONLY`면 학번이 span에 남는다 |
| 139 OpenMetrics | `obs4_openmetrics.py text` · `serve` · `prometheus`(📦) | 이름 규칙(`_seconds` · `_total` · `_bucket`)과 `# EOF` · `/metrics` scrape |
| 140 OpenInference · Phoenix | `obs6_openinference.py local` · `hide` · `phoenix` (📦) | `openinference.span.kind` · `llm.token_count.*` · 기본으로 내용을 기록한다 |
| 142 실습 | `run_all.py` | 위 결과 요약 |

## 파일

```text
part12_observability/
├── _obs.py                    # 공통: FakeLlm · weather_agent · run_turn (+ common/telemetry_util.py 다시 내보냄)
├── obs1_span_tree.py          # span 트리 · gen_ai 속성 · 스키마 v1/v2 비교
├── obs2_content_capture.py    # OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT 모드별 비교 · 개인정보 유출 검사
├── obs3_metrics.py            # ADK 내장 지표 · Plugin으로 사용자 지표 추가
├── obs4_openmetrics.py        # OpenMetrics 텍스트 · /metrics 서버 · 공식 Prometheus exporter
├── obs5_otlp_export.py        # OTLP/HTTP 전송 (Jaeger · Phoenix · Collector), --selftest 수신기
├── obs6_openinference.py      # OpenInference 계측 · Phoenix 전송 · 내용 숨기기
├── obs_agent/agent.py         # adk web · --otel_to_cloud 확인용 (🔑 Gemini)
└── run_all.py

../common/telemetry_util.py    # install_telemetry · print_span_tree · to_openmetrics (Part 14 실습 7단계와 공유)
```

## 직접 해 보기 (🔑 · 🐳)

```bash
# 1) adk web Trace 탭: 질문 후 오른쪽 이벤트 → Trace 탭에서 span 트리
adk web --port 8000

# 2) Jaeger로 보내기 (Docker): ADK 서버는 환경 변수만으로 OTLP exporter를 단다 (📦 exporter 설치 필요)
docker run --rm -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 OTEL_SERVICE_NAME=obs-lab adk web --port 8000
#    → http://localhost:16686 에서 service=obs-lab

# 3) Prometheus로 긁어 가기: obs4_openmetrics.py serve 를 켜 둔 채 prometheus.yml 에
#    scrape_configs: [{job_name: adk, static_configs: [{targets: ['127.0.0.1:9464']}]}]

# 4) Phoenix: uv pip install arize-phoenix && phoenix serve  →  uv run obs6_openinference.py phoenix
```

PowerShell에서는 환경 변수를 `$env:OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"`처럼 먼저 설정한다.

## 확인한 버전과 주의

- google-adk **2.14.0**(실습 venv)에서 실행해 확인했다(2026-11-12). opentelemetry-sdk 1.45.2.
  선택 패키지: opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-exporter-prometheus 0.66b2 ·
  openinference-instrumentation-google-adk 1.1.3 · arize-phoenix-otel 0.17.3.
- **스키마 버전**: 2.14 기본(v2)은 OTel GenAI 규약에 맞춘 형식(`invoke_workflow` 루트, `call_llm` 없음)이다.
  `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN=1`이면 이전 형식(`invocation` · `call_llm`)이고, 전역 google-adk 2.6.3도 이 모양이다.
  v1은 2027-03-31 이후 없어질 수 있다.
- **2.6.3**에는 `gen_ai.client.inference.usage.*` 카운터와 `gen_ai.invoke_workflow.duration`이 없다(나머지 지표는 같다).
- `gen_ai.*` 이름은 OpenTelemetry GenAI 의미 규약을 따른다. 이 규약은 아직 Development 단계라 이름이 바뀔 수 있다.
- OpenInference 계측을 켜면 ADK 기본 span 대신 OpenInference 이름의 span(`invocation [앱]` · `agent_run [에이전트]` · `call_llm`)이 만들어진다.
