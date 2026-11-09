# hitl_workflow — 기본 Human-in-the-Loop(HITL) 워크플로우

워크플로우 실행 도중 사람의 입력이 필요한 시점에 `RequestInput`을 발생시켜 실행을 일시 중단하고, 입력을 받은 뒤 재개하는 기본 패턴입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **중단 및 재개 메커니즘**:
  1. 워크플로우 실행 중 `RequestInput(prompt="숫자를 입력하세요:")` 노드 도달
  2. ADK Runner가 `adk_request_input` function_call 이벤트를 내며 실행 일시 멈춤
  3. 세션에서 동일한 `interrupt_id`와 `invocation_id`로 `FunctionResponse`를 전송하면 멈춘 지점부터 즉시 재개

---

## 2. 실행 방법

🟢 **LLM 키 없이 실행 가능합니다.**

```bash
cd part10_dynamic_hitl
uv run run_part10.py
```


