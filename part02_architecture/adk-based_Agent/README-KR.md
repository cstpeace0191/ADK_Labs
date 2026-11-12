# adk-based_Agent — Google ADK 기반 에이전트 프로젝트 모음

본 프로젝트 디렉터리는 **Google Agent Development Kit (ADK)**를 활용하여 구현된 표준 ADK 에이전트 패키지들을 포함하고 있습니다. 각 에이전트는 독립된 Python 모듈 및 ADK 에이전트 규격으로 구성되어 있으며, 터미널 CLI, 웹 UI, 그리고 코드 기반 Runner를 통해 즉시 실행 및 테스트할 수 있습니다.

---

## 1. 포함된 하위 에이전트 폴더 목록

| 폴더명 | 에이전트 역할 | 핵심 아키텍처 및 도구 | 주요 학습 포인트 |
|---|---|---|---|
| [**`chat_time_weather_agent`**](./chat_time_weather_agent/README-KR.md) | 세계 도시 시간·날씨 조회 및 범용 대화 비서 | Open-Meteo API 연동, `geocode`, `get_current_time`, `get_weather`, 오프라인 폴백 DB | • 도구 자동 라우팅 vs LLM 직접 응답 분기<br>• IANA Timezone 및 WMO 기상 코드 변환<br>• PEP 8 및 `AgentLoader` 호환 폴더 설계 |
| [**`memory_layers_agent`**](./memory_layers_agent/README-KR.md) | 이중 계층 메모리 (단기 세션 vs 장기 기억) 비서 | Session State (`user:name`, `trip`), Memory Service (`preload_memory`, `load_memory`) | • Session State 접두사(`user:`, `temp:`, 일반) 스코프<br>• `{key?}` 템플릿 치환을 통한 State 주입<br>• 세션 간 영속 기억 축적 및 인출 메커니즘 |

---

## 2. 전체 디렉터리 구조

```text
adk-based_Agent/
├── chat_time_weather_agent/          # 시간·날씨 및 일반 대화 에이전트
│   ├── __init__.py                  # agent 모듈 및 root_agent 노출
│   ├── agent.py                     # 도구 구현 및 에이전트 정의
│   ├── README-KR.md                 # 한국어 상세 설명서
│   └── README-EN.md                 # 영문 상세 설명서
├── memory_layers_agent/             # 이중 계층 메모리 실습 에이전트
│   ├── __init__.py                  # agent 모듈 및 root_agent 노출
│   ├── agent.py                     # State 도구 및 root_agent 정의
│   ├── README-KR.md                 # 한국어 상세 설명서
│   └── README-EN.md                 # 영문 상세 설명서
├── README-KR.md                     # 프로젝트 전체 통합 한국어 가이드 (본 문서)
└── README-EN.md                     # 프로젝트 전체 통합 영문 가이드
```

---

## 3. 사전 환경 준비 및 설정

### 1) 필수 패키지 설치
Python 3.10 이상 환경에서 Google ADK 및 의존 라이브러리를 설치합니다:

```bash
pip install google-adk python-dotenv
# 또는 uv 사용 시
uv pip install google-adk python-dotenv
```

### 2) 환경 변수(`.env`) 설정
상위 폴더(`part02_architecture` 또는 워크스페이스 루트)에 `.env` 파일을 생성하고 다음과 같이 설정합니다:

```env
# Gemini Developer API 키 (기본)
GEMINI_API_KEY=your_gemini_api_key_here

# 또는 Google Cloud Vertex AI 사용 시
# GOOGLE_GENAI_USE_VERTEXAI=TRUE
# GOOGLE_CLOUD_PROJECT=your-gcp-project-id
# GOOGLE_CLOUD_LOCATION=us-central1

# 에이전트 기본 모델 (선택)
ADK_MODEL=gemini-flash-latest

# 오프라인 테스트 모드 (0: 온라인 API, 1: 내장 오프라인 데이터)
AGENT_OFFLINE=0
```

---

## 4. 수행 및 실행 방법

본 프로젝트의 에이전트들은 다음 세 가지 수준에서 실행할 수 있습니다:

### 방법 1: ADK CLI 대화형 실행 (`adk run`)
터미널에서 에이전트와 직접 텍스트로 대화합니다:

```bash
# adk-based_Agent 디렉터리에서 실행

# 1) 시간·날씨 에이전트 실행
adk run chat_time_weather_agent

# 2) 이중 계층 메모리 에이전트 실행
adk run memory_layers_agent
```

### 방법 2: 웹 개발 UI 실행 (`adk web`)
Google ADK가 제공하는 공식 웹 인터페이스를 통해 브라우저에서 시각적으로 테스트합니다:

```bash
# adk-based_Agent 디렉터리에서 웹 서버 구동
adk web --port 8008
```
브라우저에서 `http://localhost:8008`로 접속한 후, 상단 드롭다운 메뉴에서 원하는 에이전트(`chat_time_weather_agent` 또는 `memory_layers_agent`)를 선택하여 대화를 진행합니다.

### 방법 3: Direct_ADK 연계 스크립트 실행
상위 `part02_architecture` 디렉터리에 위치한 검증 스크립트를 통해 에이전트의 내부 이벤트 생명주기 및 메모리 계층 전이를 코드로 관찰할 수 있습니다:

```bash
# part02_architecture 디렉터리로 이동
cd ..

# 1) chat_time_weather_agent의 이벤트 생명주기 관찰
uv run Direct_ADK/run_events.py

# 2) memory_layers_agent의 이중 계층 메모리(오프라인 구조 분석 / Gemini 연동 테스트) 실행
uv run Direct_ADK/run_memory_layers.py offline
uv run Direct_ADK/run_memory_layers.py llm
uv run Direct_ADK/run_memory_layers.py all
```

---

## 5. 상세 문서 링크
각 에이전트의 세부 도구 파라미터, 프롬프트 엔지니어링 지시문, 대화 시나리오 및 트러블슈팅 가이드는 각 폴더의 문서를 참조하십시오:

- [chat_time_weather_agent 상세 설명서 (README-KR.md)](./chat_time_weather_agent/README-KR.md) / [English (README-EN.md)](./chat_time_weather_agent/README-EN.md)
- [memory_layers_agent 상세 설명서 (README-KR.md)](./memory_layers_agent/README-KR.md) / [English (README-EN.md)](./memory_layers_agent/README-EN.md)

