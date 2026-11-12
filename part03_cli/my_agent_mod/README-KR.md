# my_agent_mod — ADK CLI 커스텀 날씨 에이전트

`adk create my_agent_mod` 명령어로 스캐폴딩되는 표준 에이전트 골격을 강의노트 **슬라이드 50 '첫 번째 에이전트'** 내용으로 채운 버전입니다. 커스텀 도구(`get_weather`)와 루트 `.env` 기반 인증 분기(Google AI Studio API Key / Vertex AI)를 포함하며, 특정 도시의 날씨를 물어보면 도구 함수를 호출(Function Calling)하여 답변하고 그 외 질문은 일반 지식으로 답변합니다.

---

## 1. 폴더 구조 설명

```text
my_agent_mod/
├── agent.py          # 📄 [핵심 코드] 루트 .env 로드, get_weather 도구 및 weather_agent (root_agent) 구현
├── __init__.py       # 📄 [패키지 초기화] ADK loader가 agent를 찾을 수 있도록 모듈 export (`from . import agent`)
├── README-KR.md      # 📄 [문서] 한글 가이드 문서 (본 파일)
├── README-KR.pdf     # 📄 [문서] 한글 가이드 PDF
├── README-EN.md      # 📄 [문서] 영문 가이드 문서
├── README-EN.pdf     # 📄 [문서] 영문 가이드 PDF
└── .adk/             # ⚡ [런타임 동적 생성] 로컬 실행 시 ADK가 자동 생성하는 데이터 폴더
    └── session.db    # ⚡ [동적 생성] 대화 세션 및 상태가 저장되는 로컬 SQLite 데이터베이스
```

> **참고 (`.env` 위치)**: 별도의 폴더 내 `.env` 파일 대신 실습 루트(`ADK_Labs/.env`) 파일을 `agent.py`에서 직접 로드(`Path(__file__).resolve().parents[2] / ".env"`)하여 사용합니다.

### 주요 파일 역할
- **`agent.py`**:
  1. 실습 루트(`.env`)를 로드하고 `GOOGLE_GENAI_USE_VERTEXAI` 값에 따라 **Vertex AI 모드**(`GOOGLE_CLOUD_LOCATION` 기본값 `"global"`, API 키 환경변수 제거)와 **Google AI Studio API 키 모드**(GCP 프로젝트/리전 환경변수 제거)가 충돌하지 않도록 정리합니다.
  2. 날씨 조회 함수 `get_weather(city: str) -> dict`를 정의합니다.
  3. `tools=[get_weather]`와 모델(`ADK_MODEL`, 기본값 `"gemini-flash-latest"`)을 설정한 `root_agent`(`name="weather_agent"`)를 정의합니다.
- **`__init__.py`**: `from . import agent`로 에이전트 모듈을 외부에 노출합니다.
- **`.adk/session.db`**: CLI 및 웹 실행 시 세션 히스토리가 자동으로 저장되는 SQLite 파일입니다.

---

## 2. 동작 구조 (`agent.py`)

- **엔트리포인트**: `agent.py`의 `root_agent` (`name="weather_agent"`)
- **사용 모델**: `os.getenv("ADK_MODEL", "gemini-flash-latest")`
- **역할 (`description` & `instruction`)**:
  - `description`: `"일반 질문 답변 및 도시 날씨를 알려주는 에이전트"`
  - `instruction`: `"사용자가 묻는 도시의 날씨를 get_weather로 조회해 한 문장으로 답하고, 그밖의 질문은 아느대로 답해줘."`
- **도구 (`get_weather`)**:
  ```python
  def get_weather(city: str) -> dict:
      """지정한 도시의 현재 날씨를 반환한다."""
      data = {"서울": "맑음, 18°C", "부산": "흐림, 20°C"}
      if city in data:
          return {"status": "success", "report": data[city]}
      return {"status": "error", "error_message": f"{city} 정보 없음"}
  ```

---

## 3. 실행 방법

`my_agent_mod`는 상위 폴더(`part03_cli`)에서 ADK CLI 명령어로 실행합니다:

```bash
# 1. 상위 폴더로 이동 (이미 part03_cli 위치라면 생략)
cd part03_cli

# 2. 터미널 REPL 대화 실행
adk run my_agent_mod

# 3. 인메모리 세션 모드 실행 (session.db 미사용)
adk run --in_memory my_agent_mod

# 4. 세션 저장 모드로 대화 (종료 시 my_agent_mod/s1.session.json 저장)
adk run --save_session --session_id s1 my_agent_mod

# 5. 저장된 세션 재개
adk run --resume my_agent_mod/s1.session.json my_agent_mod

# 6. 개발용 웹 UI 실행 (http://localhost:8000 접속 후 my_agent_mod 선택)
adk web --port 8000

# 7. 헤드리스 REST/SSE API 서버 실행
adk api_server --port 8000
```
