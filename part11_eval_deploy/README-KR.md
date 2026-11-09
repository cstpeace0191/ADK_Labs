# part11_eval_deploy — 에이전트 평가(Eval), A2A 통신 및 배포(Deploy)

> 강의노트 **Part 11 · 11. 평가 · 배포 · 운영**(슬라이드 110–124)과 짝을 이룬다: 평가(111) · 배포(112–122: 서버와 상태 117–118, gcloud run deploy 120, 배포 경로 121) · A2A(123).

에이전트의 품질을 정량적으로 측정하는 **ADK Eval 툴체인**, 원격 에이전트 간 협업을 위한 **A2A(Agent-to-Agent) 프로토콜**, 그리고 **Cloud Run / Agent Runtime 배포** 구성을 다룹니다.

---

## 1. 폴더 구조

```text
part11_eval_deploy/
├── weather_agent/       # 평가 대상 에이전트 + weather.evalset.json + test_config.json
├── a2a_demo/            # Agent-to-Agent 프로토콜 데모 (prime_agent 서버 + host_agent 클라이언트)
├── deploy/              # 배포: adk deploy cloud_run · gcloud run deploy(+container/) · adk deploy agent_engine · SDK (deploy/README-KR.md)
├── tests/               # 🔑 test_weather_eval.py (AgentEvaluator) · 🟢 test_container_app.py (gcloud 배포용 서버 로컬 검증)
├── make_evalset.py      # 대화 기록으로부터 ADK 표준 evalset.json 파일 생성 도구
├── run_a2a_client.py    # A2A 원격 에이전트 호출 클라이언트
├── run_server_state.py  # 🟢 서버와 상태: 인스턴스 교체 시 세션 유실 vs 바깥 DB, adk 가 고르는 SessionService (슬라이드 117–118)
└── README-KR.md            # 현재 문서
```

---

## 2. 핵심 구성 요소

### ① 에이전트 평가 (Evaluation)
- **지표**: `tool_trajectory_avg_score`(도구 호출 순서 및 인자 일치율), `response_match_score`(ROUGE-1 기반 최종 응답 유사도)
- **실행**: CLI 명령어 `adk eval` 또는 `pytest` CI 파이프라인 연동 (`AgentEvaluator.evaluate`)

### ② A2A (Agent-to-Agent) 프로토콜
- JSON-RPC 2.0 및 Agent Card 표준을 사용하여 이기종/원격 서버 간 에이전트 협업 수행
- `prime_agent`: 소수 판별 전담 A2A 서버 (포트 8001)
- `host_agent`: 원격 A2A URL을 `RemoteA2aAgent` 도구로 감싸서 질의 위임

---

## 3. 실행 방법

`part11_eval_deploy` 폴더에서 실행합니다:

### 1) CLI 평가 실행 (`adk eval`)
```bash
cd part11_eval_deploy

# CLI 평가 실행
adk eval weather_agent weather_agent/weather.evalset.json --config_file_path weather_agent/test_config.json --print_detailed_results
```

### 2) pytest CI 품질 테스트 실행
```bash
uv run pytest tests -q
```

### 3) A2A 원격 에이전트 협업 데모 실행
2개의 터미널이 필요합니다:
```bash
# 터미널 1: prime_agent A2A 서버 기동 (8001 포트)
uv run uvicorn a2a_demo.prime_agent.agent:a2a_app --port 8001

# 터미널 2: host_agent 실행 및 질의
uv run run_a2a_client.py
```

### 4) 서버와 상태 확인 (🟢 키 불필요, 슬라이드 117–118)
```bash
uv run run_server_state.py            # all
uv run run_server_state.py factory    # lost | shared | factory
```
기대 출력(google-adk 2.6.3):
```text
① [인스턴스 B] 요청 2 '내 이름이 뭐지?' → 세션 s1 없음 → 새 대화로 시작, 이름을 모른다 ✘
② [인스턴스 B] 요청 2 '내 이름이 뭐지?' → 세션 s1 발견: 이벤트 1건, State user_name='민수' ✔
③ 로컬 개발 (URI 없음)      → PerAgentDatabaseSessionService
   Cloud Run (URI 없음)     → InMemorySessionService
   URI = sqlite (DB 파일)   → SqliteSessionService
```
- Cloud Run은 `K_SERVICE` 환경변수로 감지되어 메모리 세션이 된다. 그래서 `deploy/deploy_cloud_run.sh`에 `SESSION_URI`(Cloud SQL `postgresql+asyncpg://…` 또는 `agentengine://<id>`)를 준다.
- Agent Runtime에 배포하면 `GOOGLE_CLOUD_AGENT_ENGINE_ID`가 주입되어 관리형 세션·Memory Bank가 자동으로 쓰인다. 자세히: [deploy/README-KR.md](deploy/README-KR.md)

### 5) gcloud run deploy 준비와 Agent Runtime SDK 배포 확인 (🟢, 슬라이드 120–121)
```bash
uv run pytest tests/test_container_app.py -q             # 컨테이너 서버(main.py): /list-apps · 세션 생성 · DB 저장 → 2 passed
DRY_RUN=1 bash deploy/deploy_gcloud_run.sh              # 빌드 폴더(.build_gcloud) + gcloud run deploy 명령만 출력
uv run deploy/deploy_agent_runtime_sdk.py               # AdkApp 생성 + client.agent_engines.create 설정 출력 (dry-run)
```
- `gcloud run deploy`는 **Cloud Run 전용**이다. Agent Runtime은 `adk deploy agent_engine` · `agents-cli deploy` · Python SDK로 올린다. 자세히: [deploy/README-KR.md](deploy/README-KR.md)
