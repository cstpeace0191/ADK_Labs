# my_agent — ADK CLI 기본 날씨 에이전트

`adk create` 명령어로 스캐폴딩되는 표준 에이전트 구조를 기반으로 구현된 날씨 조회 에이전트입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **역할**: 서울, 부산 등 도시 날씨를 조회하여 간결한 한 문장으로 답변합니다.
- **도구 (`get_weather`)**:
  ```python
  def get_weather(city: str) -> dict:
      """지정한 도시의 현재 날씨를 반환한다."""
      data = {"서울": "맑음, 18°C", "부산": "흐림, 20°C"}
      ...
  ```

---

## 2. 실행 방법

`part03_cli` 폴더에서 실행합니다:

```bash
cd part03_cli

# 1. 터미널 REPL 대화
adk run my_agent

# 2. 세션 저장 모드로 대화 (종료 시 s1.session.json 저장)
adk run --save_session --session_id s1 my_agent

# 3. 저장된 세션 재개
adk run --resume my_agent/s1.session.json my_agent

# 4. 웹 UI 실행 (http://localhost:8000)
adk web --port 8000
```

