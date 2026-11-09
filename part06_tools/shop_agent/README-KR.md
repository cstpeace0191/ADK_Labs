# shop_agent — 쇼핑 카트 및 결제 승인 에이전트

`ToolContext`를 활용한 세션 State 변경과 되돌리기 어려운 작업에 대한 사전 확인(`require_confirmation`) 메커니즘을 시연하는 에이전트입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **핵심 기능**:
  1. **`ToolContext` 파라미터**:
     - `add_to_cart`, `view_cart`, `checkout` 함수의 `tool_context: ToolContext` 인자는 모델의 함수 스키마에서 자동으로 제외됩니다.
     - 함수 내부에서 `tool_context.state['cart']`를 직접 조작할 수 있으며, 이 변경 사항은 이벤트의 `state_delta`로 기록됩니다.
  2. **`require_confirmation=True`**:
     ```python
     FunctionTool(func=checkout, require_confirmation=True)
     ```
     - 결제 함수 실행 전 `adk_request_confirmation` 이벤트를 발생시키고 사용자 승인 응답을 대기합니다.

---

## 2. 실행 방법

`part06_tools` 폴더에서 실행합니다:

```bash
cd part06_tools

# 스크립트 실행 (장바구니 담기 후 승인 응답 전달 과정 자동 시연)
uv run run_tools.py shop

# 터미널 대화형 실행
adk run shop_agent
```

### 대화 흐름 예시
```text
User: 마우스 하나랑 키보드 하나 장바구니에 담아줘
Agent: [add_to_cart 호출 -> state_delta: {'cart': [...]}]
Agent: 장바구니에 무선 마우스 1개와 기계식 키보드 1개를 담았습니다.
User: 결제해줘
Agent: [tool call (대기): adk_request_confirmation {'action': 'checkout'}]
Human: [승인 전달]
Agent: 결제가 성공적으로 완료되었습니다. (총액: 114,000원)
```


