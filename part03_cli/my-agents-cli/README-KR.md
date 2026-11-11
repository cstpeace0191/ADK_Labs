# my-agents-cli — Agents CLI 기반 프로덕션 에이전트 프로젝트

이 프로젝트는 Google의 차세대 에이전트 생명주기 관리 도구인 **`agents-cli`** (`version 1.13.0`)로 자동 생성된 ReAct 아키텍처 기반의 프로덕션 에이전트 프로젝트입니다.

단순 골격만을 생성하는 `adk create`와 달리, `agents-cli create`는 **FastAPI 백엔드 서버, A2A(Agent-to-Agent) 프로토콜, 단위·통합·평가(Eval) 테스트 슈트, Dockerfile, 클라우드 배포(CI/CD) 설정**을 포함하는 엔터프라이즈급 풀스택 환경을 제공합니다.

---

## 1. 프로젝트 폴더 구조

```text
my-agents-cli/
├── app/                           # 에이전트 핵심 애플리케이션 코드
│   ├── __init__.py                # 패키지 정의
│   ├── agent.py                   # ReAct 에이전트 로직 및 도구 (get_weather, get_current_time)
│   ├── fast_api_app.py            # FastAPI 백엔드 서버 (A2A Agent Card 및 추론 엔드포인트 노출)
│   └── app_utils/                 # 서비스 팩토리, 원격 텔레메트리, A2A 프로토콜 헬퍼
├── tests/                         # 포괄적인 3단계 테스트 슈트
│   ├── unit/                      # 에이전트 도구 단위 테스트 (pytest)
│   ├── integration/               # 서버 E2E 및 A2A 통신 통합 테스트
│   └── eval/                      # LLM 응답 품질 평가(Eval) 데이터셋 및 설정
├── deployment/                    # 클라우드 배포 및 인프라(Terraform) 설정
├── agents-cli-manifest.yaml       # agents-cli 프로젝트 매니페스트 (템플릿, 리전, 배포 타깃)
├── Dockerfile                     # Cloud Run / GKE 프로덕션 배포용 컨테이너 빌드 파일
├── GEMINI.md                      # AI 코딩 어시스턴트(Antigravity 등) 연동용 프로젝트 컨텍스트 가이드
├── pyproject.toml / uv.lock       # 프로젝트 독립 가상환경 및 패키지 의존성 관리
├── .env / .env.example            # Gemini / Vertex AI 인증 및 환경변수 설정
└── README-KR.md                   # (현재 문서) 프로젝트 설명서 및 단계별 수행 가이드
```

---

## 2. 사전 준비 사항 (Prerequisites)

1. **`uv` 패키지 관리자**:
   - Python 3.11+ 환경 및 패키지 격리 관리: [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
2. **`agents-cli` 도구**:
   - 글로벌 설치: `uv tool install google-agents-cli`
   - 또는 실습 환경 상위 `.venv`에 이미 설치된 `agents-cli` 사용
3. **인증 정보 설정 (`.env`)**:
   - `my-agents-cli/.env` 파일에서 환경에 맞는 인증 방식을 선택합니다:
     * **방법 ①: Google AI Studio API 키 사용** (가장 간편함):
       ```bash
       GEMINI_API_KEY=AIzaSy...
       # 아래 세 줄은 주석(#) 처리
       # GOOGLE_GENAI_USE_ENTERPRISE=true
       # GOOGLE_CLOUD_PROJECT=...
       # GOOGLE_CLOUD_LOCATION=global
       ```
     * **방법 ②: Google Cloud Vertex AI 사용**:
       ```bash
       GOOGLE_GENAI_USE_ENTERPRISE=true
       GOOGLE_CLOUD_PROJECT=<your-gcp-project-id>
       GOOGLE_CLOUD_LOCATION=global
       ```

---

## 3. 프로젝트 수행 및 실행 방법 (단계별 가이드)

모든 명령은 **`my-agents-cli` 프로젝트 폴더 내부**로 이동하여 실행합니다:

```bash
cd part03_cli/my-agents-cli
```

---

### 단계 1: 의존성 패키지 설치
`uv`를 통해 `pyproject.toml`에 정의된 패키지들을 로컬 가상환경에 설치합니다:

```bash
# agents-cli 전용 설치 명령
agents-cli install

# 또는 uv 표준 명령
uv sync
```

---

### 단계 2: 로컬 플레이그라운드 실행 (`agents-cli playground`)
개발 중 웹 브라우저에서 에이전트와 대화하고 도구 호출 과정을 실시간으로 확인할 수 있는 대화형 개발 환경을 실행합니다.

```bash
agents-cli playground
# 또는
uv run agents-cli playground
```
* 브라우저가 자동으로 열리며 (`http://localhost:8080`), `app/agent.py` 코드를 수정하고 저장하면 **자동 핫 리로드(Auto-reload)**가 동작합니다.

---

### 단계 3: CLI 단일 프롬프트 실행 (`agents-cli run`)
웹 UI 없이 터미널에서 즉시 단일 질문에 대한 에이전트의 응답을 확인합니다. 별도의 `--prompt` 플래그 없이 질문 메시지를 직접 인자(`MESSAGE`)로 전달합니다:

```bash
# 기본 단일 실행 (질문 메시지를 직접 전달)
agents-cli run "샌프란시스코의 현재 날씨 알려줘"

# 백그라운드 서버를 띄워 세션을 유지하며 대화할 때 (--start-server, --session-id)
agents-cli run --start-server --session-id s1 "안녕하세요!"
agents-cli run --session-id s1 "방금 제가 뭐라고 했나요?"
agents-cli run --stop-server  # 백그라운드 서버 종료
```

---

### 단계 4: 프로덕션 FastAPI / A2A 서버 구동
에이전트를 독립된 마이크로서비스(REST/SSE API 및 A2A 프로토콜 호환 서버)로 실행합니다:

```bash
uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 --reload
```

* **A2A Agent Card 확인**: 브라우저에서 `http://localhost:8000/.well-known/agent-card.json`에 접속하면 다른 에이전트가 이 에이전트를 탐색하고 호출할 수 있는 명세서(Agent Card)가 반환됩니다.
* **REST 호출 테스트**:
  ```bash
  curl -X POST http://localhost:8000/apps/app/users/u1/sessions/s1
  ```

---

### 단계 5: ADK CLI 도구와 연계 실행
이 프로젝트는 표준 ADK 구조(`google.adk`)를 기반으로 하므로, ADK의 범용 CLI 명령어도 그대로 호환됩니다:

```bash
# ADK 웹 개발 UI 실행
adk web --port 8008

# ADK CLI 터미널 대화
adk run app
```

---

### 단계 6: 테스트 및 코드 품질 검증 (Testing & Eval)

1. **단위 및 통합 테스트 실행**:
   ```bash
   uv run pytest tests/unit tests/integration
   ```
2. **코드 스타일 및 린트(Lint) 검사**:
   ```bash
   agents-cli lint
   ```
3. **에이전트 응답 품질 평가 (LLM Evaluation)**:
   ```bash
   agents-cli eval run
   ```
   * `tests/eval/` 디렉터리의 골든 데이터셋을 바탕으로 에이전트의 답변 품질, 도구 호출 정확도를 자동 채점합니다.

---

### 단계 7: 클라우드 배포 (Deployment)

1. **GCP 프로젝트 설정 및 인증**:
   ```bash
   gcloud auth application-default login
   gcloud config set project <YOUR_PROJECT_ID>
   ```
2. **클라우드 배포 실행**:
   ```bash
   agents-cli deploy
   ```
   * Google Cloud Vertex AI Agent Runtime 또는 Cloud Run 환경으로 자동 빌드 및 컨테이너 배포가 수행됩니다.
3. **Gemini 에코시스템 등록 (선택)**:
   ```bash
   agents-cli publish gemini
   ```

---

## 4. `adk create` vs `agents-cli create` 비교

| 비교 항목 | `adk create my_agent` (Part 3) | `agents-cli create my-agents-cli` (Part 12) |
|---|---|---|
| **설계 목적** | 빠른 학습, 프로토타이핑, 최소 코드 작성 | 엔터프라이즈 프로덕션 배포 및 팀 협업 |
| **생성 파일** | `agent.py`, `__init__.py`, `.env`, `.gitignore` (4개) | `app/`, `tests/`, `Dockerfile`, `manifest`, `GEMINI.md` 등 풀스택 |
| **A2A 프로토콜** | 미포함 (단일 에이전트) | 기본 내장 (`/.well-known/agent-card.json`) |
| **테스트 슈트** | 별도 작성 필요 | 단위(Unit), 통합(Integration), 평가(Eval) 기본 제공 |
| **개발 환경** | `adk run`, `adk web` | `agents-cli playground`, `eval run`, `deploy` |

