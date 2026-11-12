# part13_agents_cli · agents-cli 프로젝트 수명주기 (생성 → 로컬 검증 → 평가 → 배포 → 호출)

`agents-cli`(google-agents-cli 1.13.0)가 만든 실제 프로젝트 **agents-cli-workflow**를 해부해서,
실습 환경(google-adk 2.6, a2a-sdk 0.3)에서 그대로 돌아가게 옮긴 것이다.
강의노트 **Part 13 · 13. agents-cli 엔드투엔드 워크플로우**(슬라이드 143–156)와 짝을 이룬다.
개념은 Part 3 슬라이드 44–48에서 먼저 다룬다: agents-cli 소개(44) · adk와 비교(45) · 두 CLI 계층(46) · 명령 지도(47) · 명령이 내부에서 실행하는 것(48 ↔ `client.py`, `agents-cli run`). 프로젝트 구조(144 ↔ 아래 '폴더 구조')와 한 서버·두 입구(148–149 ↔ `app/fast_api_app.py`)는 Part 12에서 다룬다.
146–147번 "Coding with AI"(코딩 에이전트에 ADK 스킬·문서 MCP 연결) 설정 실습은 [`coding_with_ai/`](coding_with_ai/README-KR.md)에 있다.

```
adk 만 쓸 때                         agents-cli 를 쓸 때
──────────────                       ─────────────────────────────────────────
my_agent/agent.py                    app/agent.py  (+ App 래퍼, Gemini retry)
adk web / adk run                    agents-cli playground / agents-cli run
adk api_server                       app/fast_api_app.py  (ADK HTTP + A2A 한 서버)
adk eval  (궤적·응답 일치)            agents-cli eval run  (LLM-as-judge, 커스텀 지표)
adk deploy cloud_run|agent_engine    agents-cli deploy  (+ scaffold enhance, infra)
```

## 폴더 구조

```
part13_agents_cli/
├── agents-cli-manifest.yaml   # agents-cli 가 프로젝트 루트를 알아보는 표식 + 생성 옵션
├── app/
│   ├── agent.py               # 도구 3개 + root_agent + App(name="app")
│   ├── fast_api_app.py        # get_fast_api_app() + A2A 라우트 (lifespan 에서 부착)
│   └── app_utils/
│       ├── services.py        # shared:// → 모든 입구가 같은 Session/Artifact 서비스 사용
│       └── a2a.py             # Agent Card + JSON-RPC 라우트
├── tests/
│   ├── unit/                  # LLM 없이 도구·구성 검사 (오프라인)
│   ├── integration/           # 서버를 띄워 /run_sse, A2A, Agent Card 검사
│   └── eval/                  # agents-cli eval: 데이터셋 + eval_config.yaml + LLM 심사 함수
├── client.py                  # agents-cli run --mode adk|a2a 가 보내는 HTTP 요청 재현
├── coding_with_ai/            # 코딩 에이전트용 ADK Docs MCP 설정(mcp.json) + 동작 확인 스크립트
├── telemetry/trace_local.py   # 배포 서버와 같은 OpenTelemetry span을 로컬에서 확인 (슬라이드 154, 🟢)
├── Dockerfile · pyproject.toml · .gcloudignore   # agents-cli deploy 가 쓰는 파일
└── artifacts/                 # agents-cli eval run 결과(traces, grade_results) 예시
```

## 실습 순서

모든 명령은 `part13_agents_cli` 폴더에서 실행한다. 키는 실습 루트의 `.env`(`GOOGLE_API_KEY`, `ADK_MODEL`)를 쓴다.

> 이 PC처럼 8000 포트가 막혀 있는 Windows 환경이 있어서 예제는 **8008** 포트를 쓴다.

### 1. 단위 테스트 (키 불필요)

```bash
uv run pytest tests/unit -q
```

`AGENT_OFFLINE=1`로 외부 API 없이 도구 함수, `root_agent.name`(= manifest의 `root_agent_name`), `app.name`(= `app_name`)을 검사한다.

### 2. 서버 기동: 하나의 서버, 두 개의 입구

```bash
uv run uvicorn app.fast_api_app:app --port 8008
```

| 입구 | 경로 | 용도 |
|---|---|---|
| ADK HTTP API | `POST /apps/app/users/{u}/sessions`, `POST /run_sse` | 웹·앱 프런트엔드, SSE 스트리밍 |
| A2A | `GET /a2a/app/.well-known/agent-card.json`, `POST /a2a/app` | 다른 에이전트와 협업 (JSON-RPC) |
| 개발 UI | `GET /dev-ui/` | `agents-cli playground`가 여는 화면 (= adk web) |

`app_utils/services.py`가 `shared://` 스킴을 등록해, 두 입구가 **같은 세션 서비스**를 쓴다.

### 3. 에이전트 호출: agents-cli run 과 같은 요청을 직접 보내기

```bash
uv run client.py adk "서울의 현재 날씨와 현지 시각을 알려줘"
```

```bash
uv run client.py a2a "도쿄는 지금 몇 시야?"
```

agents-cli가 설치돼 있으면 같은 서버에 그대로 붙는다(배포된 URL에도 같은 방식).

```bash
uv run agents-cli run --url http://127.0.0.1:8008 --mode adk --app-name app "서울 날씨 알려줘"
```

```bash
uv run agents-cli run --url http://127.0.0.1:8008 --mode a2a --app-name app "도쿄는 지금 몇 시야?"
```

### 4. 평가: agents-cli eval run (LLM-as-judge)

서버를 띄운 상태에서:

```bash
uv run agents-cli eval run --url http://127.0.0.1:8008 --app-name app --dataset tests/eval/datasets/basic-dataset.json --config tests/eval/eval_config.yaml --concurrency 1 --qps 0.1
```

- `eval generate`: 데이터셋의 각 케이스를 서버에 보내 트레이스를 `artifacts/traces/`에 저장
- `eval grade`: `eval_config.yaml`의 지표로 채점 → `artifacts/grade_results/*.json|html`
  - `custom_response_quality`: `response_quality.py`의 LLM 심사(1~5점, 구조화 출력)
  - `agent_turn_count`: 인라인 파이썬 함수 지표
- 데이터셋은 두 모양을 섞어 쓸 수 있다: `prompt`(단일 질문), `agent_data.turns`(이전 대화 + 마지막 사용자 질문, "N+1" 패턴)
- 품질 게이트: `--fail-under custom_response_quality=4` → 평균이 4 미만이면 exit 1 (CI에서 사용)
- 무료 키는 분당 호출 한도가 있으므로 `--concurrency 1 --qps 0.1`로 천천히 돌린다.

`adk eval`과의 차이:

| | `adk eval` (Part 11, 실습 part11) | `agents-cli eval` |
|---|---|---|
| 데이터 | `*.evalset.json` (기대 도구 궤적·기대 응답) | `eval_cases` (prompt 또는 이전 대화, reference 선택) |
| 채점 | `tool_trajectory_avg_score`, `response_match_score` | LLM 심사·내장 지표·커스텀 함수 |
| 대상 | 로컬 에이전트 모듈 | 로컬 서버 또는 **배포된 URL** (`--url`) |
| 이후 단계 | pytest 게이트 | `compare`(회귀), `analyze`(실패 군집), `optimize`(프롬프트 자동 튜닝) |

### 5. 통합 테스트 (서버 자동 기동)

```bash
uv run pytest tests/integration -q
```

Agent Card 검사는 키 없이 통과하고, `/run_sse`·A2A 검사는 키가 있을 때만 실행된다.

### 6. 배포 (문서 기반 · 실습에서는 실행하지 않음)

agents-cli 정식 경로는 uv 프로젝트(원본 agents-cli-workflow)에서 실행한다.

```bash
gcloud config set project <your-project-id>
```

```bash
agents-cli deploy
```

- `deployment_target: agent_runtime` → 소스+Dockerfile을 Agent Runtime에 올려 **클라우드에서 빌드**, `deployment_metadata.json`에 엔진 ID 기록
- `cloud_run`으로 바꾸려면 `agents-cli scaffold enhance --deployment-target cloud_run` (코드 `app/`은 보존)
- 운영 인프라(전용 서비스 계정, Secret Manager, 관측 파이프라인): `agents-cli infra single-project --apply`
- Dev/Staging/Prod CI/CD: `agents-cli infra cicd -i` → PR마다 lint · pytest · `eval run` 자동 실행

배포 후 호출(원본 프로젝트의 실제 예):

```bash
agents-cli run --url https://us-east1-aiplatform.googleapis.com/reasoningEngines/v1/projects/<num>/locations/us-east1/reasoningEngines/<id>/api --mode a2a "서울의 날씨와 시간은?"
```

```bash
gcloud run services proxy agents-cli-workflow --region us-east1
```

```bash
agents-cli run --url http://127.0.0.1:8080 --mode adk "hello"
```

### 7. OpenTelemetry: 배포하면 켜지는 관측 파이프라인 (슬라이드 154)

agents-cli가 만든 프로젝트는 텔레메트리가 기본으로 켜진다. `app/fast_api_app.py`가
`GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true`일 때 `get_fast_api_app(otel_to_cloud=True)`로 서버를 만들고,
`agents-cli infra single-project`의 Terraform(`service.tf` · `telemetry.tf`, 원본 agents-cli-workflow)이 다음을 준비한다.

- span → **Cloud Trace**, GenAI 로그 이벤트 → **Cloud Logging** → 로그 싱크 → **BigQuery** `<프로젝트>_telemetry`
- 대화 본문은 span에 넣지 않고(`NO_CONTENT` · `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`) 완료 훅으로 **GCS** `completions/`에 jsonl로 따로 저장
- `app/agent.py`의 `name`과 manifest의 `root_agent_name`이 `gen_ai.agent.name`이 되므로 둘을 같이 바꿔야 한다

로컬에서 같은 span을 확인 (키 · 네트워크 불필요):

```bash
python telemetry/trace_local.py
```

로컬 서버를 Jaeger · Phoenix 같은 OTLP 백엔드에 연결 (📦 `uv pip install opentelemetry-exporter-otlp-proto-http`):

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 OTEL_SERVICE_NAME=agents-cli-workflow python -m uvicorn app.fast_api_app:app --port 8008
```

개념과 더 많은 실습은 [`../part12_observability/`](../part12_observability/README-KR.md) (Part 12 Observability).

## 원본(agents-cli-workflow)과 다른 점

| 항목 | 원본 | 이 실습 |
|---|---|---|
| ADK / a2a-sdk | google-adk 2.12+, a2a-sdk 1.x | google-adk 2.6, a2a-sdk 0.3 (`google.adk.a2a._compat`로 버전 차이 흡수) |
| 모델 | `gemini-3.8-flash` 고정 | `.env`의 `ADK_MODEL` 우선 (무료 키 한도 대응) |
| 도구 | Nominatim → Open-Meteo, 실패 시 오류 | Open-Meteo, 실패 시 오프라인 표(서울·도쿄·파리 등) |
| `/api/reasoning_engine` 어댑터 | Agent Runtime 콘솔 플레이그라운드용 | 생략 (`vertexai` AdkApp 필요) |
| 의존성 관리 | `uv` + `agents-cli install` | 실습 루트 `requirements.txt` (pyproject는 참고용) |
| Terraform (`deployment/terraform`) | `scaffold enhance`가 생성 | 생략 (슬라이드에서 구조만 설명) |

## 검증 결과 (2026-11-09, Windows, Gemini 무료 키 `gemini-3.5-flash-lite`)

- `pytest tests` 9 passed (unit 6 + integration 3: Agent Card, `/run_sse`, A2A `message/send`)
- `agents-cli run --mode adk` / `--mode a2a` (agents-cli 1.13.0) → 실습 서버에서 Open-Meteo 실측값으로 응답
- `agents-cli eval run --url ...` → 4건, `custom_response_quality` 평균 5.0, `agent_turn_count` 1.0 (결과: `artifacts/`)
- `uv run client.py adk|a2a` 동작

