# tutor_agent — State 템플릿 치환 튜터 에이전트

지시문(instruction) 내에 `{user:name}`, `{course}`와 같은 세션 State 변수를 동적으로 치환하여 개인화된 응답을 제공하는 에이전트입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **핵심 코드**:
  ```python
  root_agent = Agent(
      name="tutor",
      instruction="너는 {course} 과목 튜터다. 학생 {user:name}에게 친절하게 설명하라.",
      ...
  )
  ```
  세션 생성 시 주입된 `state={"course": "Agentic AI", "user:name": "김철수"}` 값이 실행 시점에 프롬프트에 자동으로 치환되어 반영됩니다.

---

## 2. 실행 방법

`part04_llm_agent` 폴더에서 실행합니다:

```bash
cd part04_llm_agent
uv run run_with_runner.py tutor
```

### 기대 출력 예시
```text
[tutor] user> Runner가 뭐예요?
final: 철수님, 안녕하세요! Agentic AI 과목 튜터입니다. Runner는 사용자의 입력 메시지를 받아...
```


