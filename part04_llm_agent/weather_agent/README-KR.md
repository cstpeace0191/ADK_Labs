# weather_agent — 도구 연동 날씨 에이전트

함수 기반의 도구(Tool) 호출과 ADK Runner의 도구 실행 메커니즘을 시연하는 에이전트입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **도구 정의**:
  ```python
  def get_weather(city: str) -> dict:
      """지정한 도시의 현재 날씨를 반환한다."""
      ...
  ```
  `tools=[get_weather]`로 에이전트에 등록되며, 사용자의 질문에 따라 모델이 자동으로 인자(`city="서울"`)를 추출하여 함수 호출(Function Call)을 발생시킵니다.

---

## 2. 실행 방법

`part04_llm_agent` 폴더에서 실행합니다:

```bash
cd part04_llm_agent
adk run weather_agent
```

또는 스크립트 실행:
```bash
uv run run_with_runner.py weather
```


