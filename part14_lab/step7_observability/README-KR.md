# step7_observability — 7단계: 학사 에이전트에 관측성 붙이기

> 강의노트 **Part 14 슬라이드 159 "실습 7단계"** 와 짝을 이루고, 개념은 **Part 12 Observability(슬라이드 130–142)** 에서 다룬다.

4단계(라우팅 워크플로우)와 5단계(HITL + Retry)를 **코드 수정 없이** OpenTelemetry로 관측한다.
에이전트 코드는 그대로 두고, 실행 전에 TracerProvider · MeterProvider만 등록한다(`common/telemetry_util.install_telemetry`).

## 실행 (🟢 키 없이)

`part14_lab` 폴더에서:

```bash
uv run run_lab.py 7
```

## 확인할 것

| # | 출력 | 의미 |
|---|---|---|
| ① | `invoke_workflow academic_workflow > invoke_node guard_input · classify_intent · grade_lookup` | 요청 1건 = trace 1개, Graph 노드마다 span 하나 |
| ② | 노드별 실행 횟수 · 평균 지연 | `fetch_registrar 3회` = 외부 API 재시도가 span으로 보인다 · 가장 느린 노드 찾기 |
| ③ | 요청별 마지막 노드 | 의도 분류(`classify_intent`)가 어디로 보냈는지 = 라우트 분포 |
| ④ | 개인정보 감사 | 주민번호 · 학번 패턴이 span 속성에 없어야 한다 (`guard_input`이 막고, 기본 설정은 내용을 기록하지 않음) |
| ⑤ | `gen_ai_invoke_workflow_duration_seconds_count/sum` | 같은 숫자를 Prometheus가 `/metrics`에서 긁어 가는 모양 (OpenMetrics) |

## 더 해 보기

- 1~3단계(LLM 에이전트)에 같은 방법을 쓰면 `generate_content` span과 토큰 지표가 추가된다 (🔑).
- `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=SPAN_ONLY`로 3단계를 실행하면 프롬프트가 span에 남는다 — ④가 왜 필요한지 확인.
- Jaeger · Phoenix로 보내기: [`../../part12_observability/obs5_otlp_export.py`](../../part12_observability/README-KR.md)
