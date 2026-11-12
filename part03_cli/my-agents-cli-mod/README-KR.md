# my-agents-cli-mod

`agents-cli create my-agents-cli_mod -y` 으로 생성된 에이전트 프로젝트에서, ./app/agent.py 를 수정한 것입니다.

---

## 프로젝트 개요 구조 (Project Structure)

```text
my-agents-cli-mod/
├── app/         # 핵심 에이전트 코드
│   ├── agent.py               # 메인 에이전트 로직
│   ├── fast_api_app.py        # FastAPI 백엔드 서버
│   └── app_utils/             # 앱 유틸리티 및 헬퍼 함수
├── tests/                     # 단위, 통합 및 평가 테스트
├── GEMINI.md                  # AI 보조 개발 가이드
└── pyproject.toml             # 프로젝트 의존성 설정
```

> 💡 **팁:** AI 지원 개발을 위해 [Antigravity CLI](https://antigravity.google/)를 사용하세요. 프로젝트 컨텍스트가 `GEMINI.md`에 사전 구성되어 있습니다.

---

## 요구 사항 (Requirements)

시작하기 전에 다음 도구들이 설치되어 있는지 확인하세요:
- **uv**: Python 패키지 관리자 (본 프로젝트의 모든 의존성 관리에 사용) - [설치 안내](https://docs.astral.sh/uv/getting-started/installation/) (`uv add <패키지>`로 [패키지 추가](https://docs.astral.sh/uv/concepts/dependencies/))
- **agents-cli**: Google Agents CLI - `uv tool install google-agents-cli` 명령으로 설치
- **Google Cloud SDK**: GCP 서비스 이용을 위한 SDK - [설치 안내](https://cloud.google.com/sdk/docs/install)

---

## 빠른 시작 (Quick Start)

아직 설치되지 않은 경우 `agents-cli` 및 관련 스킬을 설치합니다:

```bash
uvx google-agents-cli setup
```

필요한 패키지를 설치합니다:

```bash
agents-cli install
```

로컬 웹 서버 환경에서 에이전트를 테스트합니다:

```bash
agents-cli playground
```

`uv run adk` 명령을 통해 [ADK](https://adk.dev/) CLI 기능들도 함께 활용할 수 있습니다.

---

## 명령어 안내 (Commands)

| 명령어 | 설명 |
| :--- | :--- |
| `agents-cli install` | uv를 사용하여 의존성 패키지 설치 |
| `agents-cli playground` | 로컬 개발 환경(대화형 UI) 실행 |
| `agents-cli lint` | 코드 품질 및 스타일 검사 실행 |
| `agents-cli eval` | 에이전트 동작 평가 (생성, 채점, 분석 등 — `agents-cli eval --help` 참조) |
| `uv run pytest tests/unit tests/integration` | 단위 및 통합 테스트 실행 |
| `agents-cli deploy` | 에이전트를 Google Cloud Agent Runtime에 배포 |
| `agents-cli publish gemini` | 배포된 에이전트를 Gemini에 등록 |
| [A2A Inspector](https://github.com/a2aproject/a2a-inspector) | A2A(Agent-to-Agent) 프로토콜 인스펙터 실행 |

---

## 🛠️ 프로젝트 관리 (Project Management)

| 명령어 | 수행 작업 |
| :--- | :--- |
| `agents-cli scaffold enhance` | CI/CD 파이프라인 및 Terraform 인프라 코드 추가 |
| `agents-cli infra cicd` | 단일 명령어로 전체 CI/CD 파이프라인 및 인프라 원클릭 설정 |
| `agents-cli scaffold upgrade` | 사용자 정의 수정 사항을 보존하면서 최신 템플릿 버전으로 자동 업그레이드 |

---

## 개발 (Development)

`app/agent.py`에서 에이전트 로직을 수정하고 `agents-cli playground`로 테스트하세요. 파일 저장 시 코드가 자동으로 다시 로드(Hot-Reload)됩니다.

---

## 배포 (Deployment)

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

- CI/CD 및 Terraform 코드를 추가하려면 `agents-cli scaffold enhance` 명령을 실행하세요.
- 프로덕션 인프라를 프로비저닝하려면 `agents-cli infra cicd` 명령을 실행하세요.

---

## 관측 가능성 (Observability)

Cloud Trace, BigQuery, Cloud Logging으로 텔레메트리(원격 측정) 데이터가 자동 내보내기(Export)되도록 기본 내장되어 있습니다.

---

## A2A 인스펙터 (A2A Inspector)

이 에이전트는 [A2A 프로토콜(Agent-to-Agent Protocol)](https://a2a-protocol.org/)을 기본 지원합니다. 다른 에이전트와의 상호 운용성을 테스트하려면 [A2A Inspector](https://github.com/a2aproject/a2a-inspector)를 사용하세요.  
자세한 내용은 [A2A Inspector 문서](https://github.com/a2aproject/a2a-inspector)를 참조하시기 바랍니다.

---
---

# 📂 `my-agents-cli-mod` 상세 폴더 구조 및 동적 생성 여부 분석

`my-agents-cli-mod` 프로젝트를 구성하는 전체 폴더 및 파일의 역할과 **생성 시점(초기 스캐폴딩 vs 동적 생성 vs 사용자 수정)**을 상세히 정리한 가이드입니다.

```text
my-agents-cli-mod/
├── 📁 app/                             # [초기 생성] 핵심 에이전트 애플리케이션 코드
│   ├── 📄 agent.py                     # ✏️ [초기 생성 / 사용자 수정] 에이전트 코어 로직 및 도구 정의
│   ├── 📄 fast_api_app.py              # 🟢 [초기 생성] REST / SSE / A2A 지원 FastAPI 서버
│   ├── 📄 __init__.py                  # 🟢 [초기 생성] Python 패키지 선언
│   ├── 📁 app_utils/                   # 🟢 [초기 생성] 에이전트 보조 유틸리티 모듈
│   │   ├── 📄 a2a.py                   # 🟢 [초기 생성] A2A 프로토콜 통신 및 Agent Card 처리
│   │   ├── 📄 reasoning_engine.py      # 🟢 [초기 생성] Vertex AI Reasoning Engine 래퍼
│   │   └── 📄 services.py              # 🟢 [초기 생성] ADK 세션 및 아티팩트 서비스 팩토리
│   ├── 📁 .adk/                        # ⚡ [동적 생성 - 런타임] 로컬 실행 시 자동 생성되는 내부 데이터 폴더
│   │   └── 📄 session.db               # ⚡ [동적 생성 - 런타임] 로컬 실행 중 세션·대화 상태가 기록되는 SQLite DB
│   └── 📁 __pycache__/                 # ⚡ [동적 생성 - 컴파일] Python 인터프리터 바이트코드 캐시
│
├── 📁 deployment/                      # ⚡ [동적 생성 - scaffold enhance] 인프라 및 배포 코드 디렉터리
│   └── 📁 terraform/                   # ⚡ [동적 생성 - scaffold enhance] GCP 리소스 배포용 Terraform HCL 코드
│       ├── 📁 shared/                  # ⚡ [동적 생성] 공유 인프라 모듈
│       └── 📁 single-project/          # ⚡ [동적 생성] 단일 프로젝트 배포 스크립트 (main.tf 등)
│
├── 📁 tests/                           # 🟢 [초기 생성] 에이전트 테스트 및 평가 디렉터리
│   ├── 📁 unit/                        # 🟢 [초기 생성] 단위 테스트 디렉터리
│   │   └── 📄 test_dummy.py            # 🟢 [초기 생성] 기본 단위 테스트 샘플
│   ├── 📁 integration/                 # 🟢 [초기 생성] 서버 통합 테스트 디렉터리
│   │   └── 📄 test_server_e2e.py       # 🟢 [초기 생성] FastAPI 및 A2A 엔드포인트 E2E 테스트
│   └── 📁 eval/                        # 🟢 [초기 생성] 에이전트 평가(Evaluation) 파이프라인
│       ├── 📄 eval_config.yaml         # 🟢 [초기 생성] 평가 지표 및 설정 파일
│       ├── 📄 response_quality.py      # 🟢 [초기 생성] LLM 응답 품질 자동 채점기
│       └── 📁 datasets/                # 🟢 [초기 생성] 평가 질문 데이터셋 폴더
│           └── 📄 basic-dataset.json   # 🟢 [초기 생성] 평가용 질의 및 기대 응답 데이터
│
├── 📁 .venv/                           # ⚡ [동적 생성 - 패키지 설치] `agents-cli install` / `uv sync` 실행 시 생성된 가상환경
├── 📁 .pytest_cache/                   # ⚡ [동적 생성 - 테스트] `pytest` 실행 시 생성되는 테스트 결과 캐시
│
├── 📄 agents-cli-manifest.yaml         # 🟢 [초기 생성] agents-cli 메타데이터 (템플릿, 에이전트 이름, 대상 런타임)
├── 📄 pyproject.toml                   # 🟢 [초기 생성] uv 기반 Python 프로젝트 설정 및 의존성 명세
├── 📄 uv.lock                          # ⚡ [동적 생성 - 패키지 설치] `agents-cli install` 실행 시 생성되는 패키지 버전 잠금 파일
├── 📄 deployment_metadata.json         # ⚡ [동적 생성 - 배포] `agents-cli deploy` 성공 시 생성되는 원격 엔진 ID 및 배포 이력
├── 📄 Dockerfile                       # 🟢 [초기 생성] 컨테이너 기반 빌드 및 배포를 위한 도커 명세서
├── 📄 .env                             # 🟢 [초기 생성 / 사용자 설정] API 키, 모델명, 환경 설정값 파일
├── 📄 .env.example                     # 🟢 [초기 생성] 환경 설정 예시 템플릿
├── 📄 .gitignore                       # 🟢 [초기 생성] Git 형상 관리 제외 규칙
├── 📄 .gcloudignore                    # 🟢 [초기 생성] GCP 배포 시 업로드 제외 규칙
├── 📄 GEMINI.md                        # 🟢 [초기 생성] Antigravity/Gemini 코딩 에이전트용 프로젝트 가이드 문서
├── 📄 README.md                        # 🟢 [초기 생성] 원본 영문 가이드 문서
└── 📄 README-KR.md                     # ✏️ [사용자 추가 문서] 한글 번역 및 폴더 구조 상세 설명서 (본 파일)
```

---

## 📊 파일/폴더 분류 기준 안내

| 구분 아이콘 | 분류명 | 상세 설명 | 대표 파일 / 폴더 |
| :---: | :--- | :--- | :--- |
| 🟢 | **초기 스캐폴딩 생성** | `agents-cli create` 명령을 통해 템플릿으로부터 최초 프로젝트 생성 시 자동 구성되는 파일 | `app/fast_api_app.py`, `tests/`, `Dockerfile`, `agents-cli-manifest.yaml` |
| ⚡ | **동적 생성 (런타임/명령)** | 프로젝트 초기 생성 시점에는 없었으나, 특정 명령어 실행(`install`, `enhance`, `deploy`, `run`, `pytest`) 또는 런타임 동작 시 사후 자동 생성되는 파일 및 디렉터리 | `.venv/`, `uv.lock`, `deployment/`, `deployment_metadata.json`, `app/.adk/session.db`, `.pytest_cache/` |
| ✏️ | **초기 생성 및 사용자 수정** | 템플릿으로 제공된 골격을 바탕으로 개발자가 비즈니스 요구사항에 맞게 직접 편집하거나 추가한 파일 | `app/agent.py`, `.env`, `README-KR.md` |

