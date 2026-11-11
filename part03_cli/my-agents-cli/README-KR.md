# my-agents-cli

간단한 ReAct 에이전트
`agents-cli` 버전 `1.13.0`으로 생성된 에이전트 프로젝트입니다.

## 프로젝트 폴더 구조 (Project Structure)

이 프로젝트는 `agents-cli create` 명령으로 최초 스캐폴딩(scaffolded)된 정적 파일들과, 런타임 실행 및 확장 명령어를 통해 동적으로 생성되는 파일 및 디렉터리들로 구성되어 있습니다.

```text
my-agents-cli/
├── app/                              # [정적] 핵심 에이전트 애플리케이션 코드
│   ├── agent.py                      # [정적] 메인 에이전트 로직 (root_agent 정의, 도구, 지시문)
│   ├── fast_api_app.py               # [정적] 에이전트 엔드포인트를 제공하는 FastAPI 백엔드 서버
│   ├── __init__.py                   # [정적] 애플리케이션 패키지 진입점
│   ├── app_utils/                    # [정적] 헬퍼 유틸리티
│   │   ├── a2a.py                    # [정적] A2A (Agent-to-Agent) 프로토콜 카드 및 유틸리티
│   │   ├── reasoning_engine.py       # [정적] Vertex AI 추론 엔진(Reasoning Engine) 연동 모듈
│   │   └── services.py               # [정적] 세션 및 메모리 서비스 초기화 모듈
│   └── .adk/                         # ⚡ [동적 - 런타임] ADK / Playground 실행 시 런타임에 자동 생성
│       └── session.db                # ⚡ [동적 - 런타임] 대화 세션 및 상태(State)를 보관하는 로컬 SQLite DB
├── tests/                            # [정적] 테스트 스위트
│   ├── unit/                         # [정적] 단위 테스트 (예: test_dummy.py)
│   ├── integration/                  # [정적] E2E 통합 테스트 (test_server_e2e.py, test_agent_card.py)
│   └── eval/                         # [정적] 에이전트 평가(Evaluation) 스위트
│       ├── datasets/                 # [정적] 평가 데이터셋 정의 (예: basic-dataset.json)
│       ├── eval_config.yaml          # [정적] 평가 메트릭 및 평가 기준 설정 파일
│       └── response_quality.py       # [정적] 응답 품질 평가 로직
├── deployment/                       # 🛠️ [동적 - 명령어] `agents-cli scaffold enhance` 실행 시 생성
│   └── terraform/                    # 🛠️ [동적 - 명령어] GCP 클라우드 인프라 구성을 위한 Terraform IaC 모듈
├── .google-agents-cli/               # ⚡ [동적 - 런타임] agents-cli CLI 실행 시 생성되는 캐시/상태 디렉터리
│   └── run_state.json                # ⚡ [동적 - 런타임] 로컬 명령어 실행 상태 및 캐시 파일
├── .venv/                            # ⚡ [동적 - 환경설정] `agents-cli install` / `uv`로 생성되는 가상환경
├── uv.lock                           # ⚡ [동적 - 환경설정] uv 패키지 매니저가 자동 생성/관리하는 의존성 락파일
├── deployment_metadata.json          # 🛠️ [동적 - 명령어] 빌드 및 배포 단계에서 생성되는 배포 메타데이터
├── .env                              # ⚙️ [사용자 설정] 로컬 환경변수 파일 (.env.example에서 복사하여 생성)
├── .env.example                      # [정적] 환경변수 템플릿 파일
├── .gcloudignore                     # [정적] GCP 배포 패키징 시 제외할 파일 목록
├── .gitignore                        # [정적] Git 버전 관리 제외 목록
├── agents-cli-manifest.yaml          # [정적] 프로젝트 매니페스트 (기본 템플릿, 에이전트 런타임 설정)
├── Dockerfile                        # [정적] Cloud Run / Agent Runtime 배포용 컨테이너 빌드 정의서
├── GEMINI.md                         # [정적] Antigravity AI 어시스턴트를 위한 컨텍스트 가이드
├── pyproject.toml                    # [정적] 프로젝트 설정 및 패키지 의존성 정의 (uv 기반)
├── README.md (READ.md)               # [정적] 영문 프로젝트 설명서
└── README-KR.md (READ-KR.md)         # ✍️ [문서] 한글 프로젝트 설명서
```

### 범례 (Legend)
- **`[정적 (Static)]`**: 프로젝트 생성 시점(`agents-cli create`)에 기본 생성되는 파일.
- **`⚡ [동적 - 런타임 (Dynamic - Runtime)]`**: 에이전트 서버 실행(`agents-cli playground`, `adk web`, 테스트 등) 시 자동으로 생성되는 파일/폴더.
- **`⚡ [동적 - 환경설정 (Dynamic - Setup)]`**: 패키지 설치(`agents-cli install` / `uv sync`) 시 자동으로 구축/생성되는 환경 및 락파일.
- **`🛠️ [동적 - 명령어 (Dynamic - Command)]`**: 인프라 확장 명령어(`agents-cli scaffold enhance`, `agents-cli infra`) 실행 시 생성되는 파일/폴더.
- **`⚙️ [사용자 설정 (User / Config)]`**: 개발자가 직접 설정하거나 템플릿에서 복사하여 사용하는 파일.

> 💡 **팁:** AI 지원 개발을 위해 [Antigravity CLI](https://antigravity.google/)를 사용할 수 있으며, 프로젝트 컨텍스트는 `GEMINI.md`에 사전 구성되어 있습니다.

## 필수 요구 사항 (Requirements)

시작하기 전에 다음 항목이 설치되어 있는지 확인하세요:
- **uv**: Python 패키지 매니저 (이 프로젝트의 모든 의존성 관리에 사용) - [설치 안내](https://docs.astral.sh/uv/getting-started/installation/) (`uv add <패키지명>`으로 [패키지 추가](https://docs.astral.sh/uv/concepts/dependencies/))
- **agents-cli**: Agents CLI - `uv tool install google-agents-cli` 명령어로 설치
- **Google Cloud SDK**: GCP 클라우드 서비스 연동용 - [설치 안내](https://cloud.google.com/sdk/docs/install)

## 빠른 시작 (Quick Start)

`agents-cli` 및 관련 스킬이 아직 설치되지 않은 경우 설치합니다:

```bash
uvx google-agents-cli setup
```

필요한 패키지를 설치합니다:

```bash
agents-cli install
```

로컬 웹 서버로 에이전트를 테스트합니다:

```bash
agents-cli playground
```

`adk` 명령어를 사용하여 [ADK](https://adk.dev/) CLI 기능도 활용할 수 있습니다.

## 명령어 목록 (Commands)

| 명령어 | 설명 |
| --- | --- |
| `agents-cli install` | uv를 사용하여 프로젝트 의존성 패키지 설치 |
| `agents-cli playground` | 로컬 개발 환경(Playground 웹 UI) 실행 |
| `agents-cli lint` | 코드 품질 검사 실행 |
| `agents-cli eval` | 에이전트 동작 평가 (생성, 채점, 분석 등 — `agents-cli eval --help` 참조) |
| `uv run pytest tests/unit tests/integration` | 단위 및 통합 테스트 실행 |
| `agents-cli deploy` | Agent Runtime으로 에이전트 배포 |
| `agents-cli publish gemini` | 배포된 에이전트를 Gemini에 등록 |
| [A2A Inspector](https://github.com/a2aproject/a2a-inspector) | A2A 프로토콜 인스펙터 실행 |

## 🛠️ 프로젝트 관리 (Project Management)

| 명령어 | 수행 작업 |
| --- | --- |
| `agents-cli scaffold enhance` | CI/CD 파이프라인 및 Terraform 인프라 코드 추가 |
| `agents-cli infra cicd` | 전체 CI/CD 파이프라인 및 인프라 원클릭 자동 설정 |
| `agents-cli scaffold upgrade` | 사용자 커스텀 코드를 유지하면서 최신 버전으로 자동 업그레이드 |

---

## 개발 (Development)

`app/agent.py`에서 에이전트 로직을 수정하고 `agents-cli playground`로 테스트하세요. 파일 저장 시 자동으로 리로드됩니다.

## 배포 (Deployment)

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

CI/CD 파이프라인과 Terraform을 추가하려면 `agents-cli scaffold enhance`를 실행하세요.  
운영 인프라를 프로비저닝하려면 `agents-cli infra cicd`를 실행하세요.

## 관측성 (Observability)

Cloud Trace, BigQuery, Cloud Logging으로 원격 분석 데이터를 내보내는 텔레메트리(Telemetry) 기능이 기본 내장되어 있습니다.

## A2A Inspector

이 에이전트는 [A2A Protocol](https://a2a-protocol.org/)을 지원합니다. 상호 운용성을 테스트하려면 [A2A Inspector](https://github.com/a2aproject/a2a-inspector)를 사용하세요.  
자세한 내용은 [A2A Inspector 문서](https://github.com/a2aproject/a2a-inspector)를 참조하세요.

