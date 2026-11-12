# my_agent_mod — ADK CLI 기본 날씨 에이전트

`adk create my_agent_mod` 명령어로 스캐폴딩되는 표준 에이전트 구조를 기반으로, 커스텀 도구(`get_current_weather`)를 추가 구현한 날씨 조회 에이전트입니다. 대화형 모델이 사용자 질문에 답하면서 특정 도시의 날씨를 물어보면 도구 함수를 호출(Function Calling)하여 정확한 정보를 전달합니다.

---

## 1. 폴더 구조 설명

```text
my_agent_mod/
├── agent.py          # 📄 [핵심 코드] get_weather 도구 및 weather_agent (root_agent) 구현
├── __init__.py       # 📄 [패키지 초기화] ADK loader가 agent를 찾을 수 있도록 모듈 export (`from . import agent`)
├── .env              # ⚙️ [환경 설정] 모델명(ADK_MODEL) 및 API 키 설정
├── .gitignore        # ⚙️ [Git 설정] 세션 DB 및 로컬 캐시 제외 규칙
├── README-KR.md      # 📄 [문서] 한글 가이드 문서 (본 파일)
├── README.md         # 📄 [문서] 영문 기본 안내 문서
└── .adk/             # ⚡ [런타임 동적 생성] 로컬 실행 시 ADK가 자동 생성하는 데이터 폴더
    └── session.db    # ⚡ [동적 생성] 대화 세션 및 상태가 저장되는 로컬 SQLite 데이터베이스
```

### 주요 파일 역할
- **`agent.py`**: 날씨 조회 함수 `get_weather(city: str) -> dict`를 선언하고, 이를 `tools=[get_weather]`로 등록한 `weather_agent`(`root_agent`)를 정의합니다.
- **`__init__.py`**: `from . import agent`로 에이전트 모듈을 외부에 노출합니다.
- **`.adk/session.db`**: CLI 대화 진행 시 세션 히스토리가 자동으로 저장되는 SQLite 파일입니다.

---

## 2. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **역할**: 서울, 부산 등 도시 날씨를 조회하여 간결한 한 문장으로 답변하며, 그 외 질문은 일반 상식으로 답변합니다.
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

# 6. 개발용 웹 UI 실행 (http://localhost:8000 접속)
adk web --port 8000

# 7. 헤드리스 REST/SSE API 서버 실행
adk api_server --port 8000
```

`adk api_server`는 `/`에 브라우저 페이지를 제공하지 않으므로 `http://localhost:8000/` 요청의 `404 Not Found`는 정상입니다. 브라우저 UI를 사용하려면 API 서버를 `Ctrl+C`로 종료한 뒤 `part03_cli` 폴더에서 `adk web --port 8000`을 실행하세요. API 서버는 `/docs`, `/run` 등의 REST/SSE 요청용입니다.
