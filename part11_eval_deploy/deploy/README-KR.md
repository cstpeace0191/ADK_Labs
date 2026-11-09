# deploy — 클라우드 배포 스크립트 및 컨테이너 정의

> 강의노트 **Part 11 · 11. 평가 · 배포 · 운영**: 배포 대상(112) · Cloud Run(113) · Agent Runtime(114) · 비교(115–116) · **서버와 상태(117–118)** · Cloud Run 배포(119) · **gcloud run deploy(120)** · **배포 경로 정리(121)** · Agent Runtime 배포와 트리거(122)

ADK 에이전트(`../weather_agent`)를 **Google Cloud Run**과 **Agent Runtime**(구 Agent Engine, Vertex AI)에 배포하는 스크립트와 컨테이너 예시다.
실습 시간에는 배포하지 않는다(GCP 프로젝트·결제 필요). 배포 전에 `../run_server_state.py`(🟢 키 불필요)로 '상태를 누가 책임지나'를 먼저 확인한다.

---

## 1. 파일 구성

| 파일 | 하는 일 |
|---|---|
| `deploy_cloud_run.sh` | `adk deploy cloud_run` — ADK가 서버 컨테이너를 만들어 Cloud Run에 올린다. 세션·파일·기억 저장소는 `SESSION_URI` · `ARTIFACT_URI` · `MEMORY_URI` 로 **내가** 지정한다 |
| `deploy_agent_runtime.sh` | `runtime`: `adk deploy agent_engine` — 서버 호스팅·세션·Memory Bank를 **플랫폼이** 제공 · `pubsub`: Pub/Sub 트리거 Cloud Run 배포 예시 |
| `deploy_gcloud_run.sh` | **`gcloud run deploy --source .`** — 빌드 폴더(`.build_gcloud/` = `container/*` + `weather_agent/`)를 만들고 Cloud Run에 배포, 키는 `--set-secrets`, 호출 확인은 ID 토큰 (`DRY_RUN=1`: 명령만 출력) |
| `deploy_agent_runtime_sdk.py` | Agent Runtime **Python SDK** 배포: `AdkApp(agent=root_agent)` → `client.agent_engines.create(...)` (기본 dry-run, `--deploy`로 실제 배포) |
| `container/` | gcloud 배포용 서버: `main.py`(get_fast_api_app, `SESSION_SERVICE_URI`) · `Dockerfile`(비루트 사용자, `uvicorn main:app --port $PORT`) · `requirements.txt` · `.dockerignore` |
| `../tests/test_container_app.py` | 🟢 배포 전 로컬 검증: 빌드 폴더를 임시로 만들어 `/list-apps` · 세션 생성 · DB 저장 확인 |

## 2. 실행 (part11_eval_deploy 폴더에서)

스크립트는 `./weather_agent` 를 배포하므로 **`part11_eval_deploy` 폴더에서** 실행한다.

```bash
cd part11_eval_deploy
export GOOGLE_CLOUD_PROJECT=<project-id>
export GOOGLE_CLOUD_LOCATION=asia-northeast3

# Cloud Run: 상태 저장소를 내가 연결한다
export SESSION_URI="postgresql+asyncpg://user:pass@host:5432/adk"   # 또는 agentengine://<id> (세션만 Agent Runtime에)
bash deploy/deploy_cloud_run.sh

# Agent Runtime: 플랫폼이 세션·Memory Bank를 붙여 준다
bash deploy/deploy_agent_runtime.sh runtime
```

## 3. gcloud run deploy로 Cloud Run 배포 (슬라이드 120)

`adk deploy cloud_run`은 에이전트 폴더만 주면 ADK가 서버와 Dockerfile을 만든다. `gcloud run deploy`는 **서버 코드(main.py)와 Dockerfile을 내가 쓰고** 그 폴더를 올린다.

```bash
cd part11_eval_deploy
python -m pytest tests/test_container_app.py -q          # ① 로컬 검증 (키 불필요)
DRY_RUN=1 bash deploy/deploy_gcloud_run.sh               # ② 빌드 폴더 + 명령 확인

# ③ 실제 배포 (GCP 필요): AI Studio 키는 Secret Manager 에 먼저 저장
printf '%s' "$GOOGLE_API_KEY" | gcloud secrets create gemini-api-key --data-file=-
export SESSION_SERVICE_URI="postgresql+asyncpg://user:pass@host:5432/adk"
bash deploy/deploy_gcloud_run.sh                         # = gcloud run deploy weather-agent --source . ...
```

- `--source .` → Cloud Build가 Dockerfile로 이미지를 만들고 Artifact Registry에 넣은 뒤 새 리비전을 띄운다(로컬 Docker 불필요).
- `--no-allow-unauthenticated`(비공개) → `TOKEN=$(gcloud auth print-identity-token)`을 `Authorization: Bearer`로 붙여 `/list-apps`, `/apps/weather_agent/users/u1/sessions/s1`, `/run_sse`를 호출한다.
- 키를 이미지나 `--set-env-vars`에 평문으로 넣지 않는다. `--set-secrets=GOOGLE_API_KEY=gemini-api-key:latest` (서비스 계정에 `roles/secretmanager.secretAccessor`). Vertex AI(`USE_VERTEXAI=TRUE`)면 키 없이 서비스 계정 권한으로 호출한다.

## 4. Agent Runtime은 gcloud run deploy로 올리지 않는다 (슬라이드 121)

`gcloud run deploy`는 **Cloud Run 서비스만** 만든다. Agent Runtime(구 Agent Engine)은 다음 중 하나로 올린다.

| 방법 | 명령 | 이 폴더 |
|---|---|---|
| ADK CLI | `adk deploy agent_engine --project … --region … --display_name … ./weather_agent` | `deploy_agent_runtime.sh runtime` |
| agents-cli | `agents-cli deploy` (기본 대상 Agent Runtime) | `../../part12_agents_cli/` |
| Python SDK | `vertexai.Client(...).agent_engines.create(agent=AdkApp(agent=root_agent), config={requirements, staging_bucket})` | `deploy_agent_runtime_sdk.py` |
| SDK (Dockerfile · 이미지) | `client.runtimes.create(config={"image_spec": {}} 또는 {"container_spec": {"image_uri": …}})` — google-cloud-aiplatform ≥ 1.144, 런타임 계약 준수 | (실습 환경 1.132에는 없음) |

## 5. 서버와 상태: 누가 책임지나 (슬라이드 117–118)

| 책임 | Cloud Run (내가) | Agent Runtime (플랫폼이) |
|---|---|---|
| 서버 | ADK가 만든 컨테이너(또는 `container/main.py`)를 실행 | 플랫폼이 호스팅 · 확장 (Vertex AI API 경유) |
| 세션 · State | `--session_service_uri` 로 직접 연결. **없으면 메모리 → 유실** | `GOOGLE_CLOUD_AGENT_ENGINE_ID` 주입 → VertexAiSessionService 자동 |
| 장기 기억 | `--memory_service_uri` 로 직접 지정 | Memory Bank 내장 |
| 인증 · 관측 | IAM 또는 공개, Logging · Trace 직접 구성 | Vertex AI IAM, Cloud Trace · 콘솔 통합 |

주의할 점(google-adk 2.6.3 기준):
- URI 없이 Cloud Run에 올리면 ADK가 `K_SERVICE` 환경변수로 Cloud Run을 감지해 **InMemorySessionService**를 쓴다.
- `container/main.py`의 기본값 `sqlite+aiosqlite:///./sessions.db`도 **컨테이너 안의 파일**이라 인스턴스마다 따로 생기고 교체되면 사라진다. 운영에서는 반드시 `SESSION_SERVICE_URI`를 바깥 DB로 지정한다.
- PostgreSQL은 비동기 엔진을 쓰므로 `postgresql+asyncpg://` 형식이다.
- `--trigger_oidc_*` 플래그(Pub/Sub 트리거 인증)는 2.13 이상에만 있다. 2.6.3에는 `--trigger_sources`만 있다.
