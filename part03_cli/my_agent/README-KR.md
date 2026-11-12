# my_agent — ADK 기본 에이전트

`adk create my_agent` 명령어로 생성되는 가장 기본적이고 표준적인 ADK(Agent Development Kit) 에이전트입니다. 별도의 커스텀 도구(Tool) 없이 대형 언어 모델(Gemini) 본연의 추론 능력을 통해 사용자의 일반적인 질문에 답변합니다.

---

## 1. 폴더 구조 설명

```text
my_agent/
├── agent.py          # 📄 [핵심 코드] root_agent 정의 (Agent/LlmAgent 선언 및 프롬프트 설정)
├── __init__.py       # 📄 [패키지 초기화] ADK loader가 agent를 찾을 수 있도록 모듈 export (`from . import agent`)
├── .env              # ⚙️ [환경 설정] 모델명(ADK_MODEL) 및 API 키 설정
├── .gitignore        # ⚙️ [Git 설정] 세션 DB 및 가상환경 등 제외 규칙
└── .adk/             # ⚡ [런타임 동적 생성] 로컬 실행 시 ADK가 자동 생성하는 데이터 폴더
    └── session.db    # ⚡ [동적 생성] 대화 세션 및 상태가 저장되는 로컬 SQLite 데이터베이스
```

### 주요 파일 역할
- **`agent.py`**: ADK의 기본 진입점(Entry Point)입니다. `root_agent` 객체에 모델(`gemini-3.5-flash`), 에이전트 이름(`root_agent`), 설명(Description), 기본 지침(Instruction)이 정의되어 있습니다.
- **`__init__.py`**: `from . import agent` 구문을 통해 ADK의 `AgentLoader`가 디렉터리 이름(`my_agent`)만으로 에이전트를 인식하고 로드할 수 있게 합니다.
- **`.adk/session.db`**: `adk run` 또는 `adk web` 실행 시 대화 상태를 지속 관리하기 위해 자동 생성되는 SQLite 데이터베이스입니다.

---

## 2. 실행 방법

`my_agent`는 상위 폴더(`part03_cli`)에서 ADK CLI 명령어로 실행합니다.

```bash
# 1. 상위 폴더로 이동 (이미 part03_cli 위치라면 생략)
cd part03_cli

# 2. 터미널 REPL 대화 실행
adk run my_agent

# 3. 인메모리 세션으로 실행 (session.db를 생성/사용하지 않음)
adk run --in_memory my_agent

# 4. 세션 저장 모드로 실행 (종료 시 my_agent/s1.session.json 생성)
adk run --save_session --session_id s1 my_agent

# 5. 저장된 세션 재개하여 대화 이어가기
adk run --resume my_agent/s1.session.json my_agent

# 6. 개발용 웹 UI 실행 (브라우저에서 http://localhost:8000 접속)
adk web --port 8000

# 7. 헤드리스 REST/SSE API 서버 실행
adk api_server --port 8000
```

