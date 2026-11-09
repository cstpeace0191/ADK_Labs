# refund_agent — 장기 실행(LongRunningFunctionTool) 환불 에이전트

외부 시스템의 비동기 승인이나 관리자의 결재가 필요한 작업을 처리하는 `LongRunningFunctionTool` 패턴 에이전트입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent` (`refund_agent`)
- **작업 흐름**:
  1. 사용자가 환불 요청: `ORD-1001 50000원 환불해줘`
  2. 모델이 `request_refund` 도구를 호출:
     - 도구는 즉시 결과를 확정짓지 않고 `status: pending`, `ticket: TICKET-0001`을 반환
  3. Runner는 해당 도구 호출 ID(`function_call.id`)를 `long_running_tool_ids`에 등록하고 대기
  4. 외부 관리자가 승인한 후, 동일한 `function_call.id`를 가진 `FunctionResponse`를 세션에 주입하면 에이전트가 최종 환불 완료 안내 메시지를 출력

---

## 2. 실행 방법

`part06_tools` 폴더에서 실행합니다:

```bash
cd part06_tools
uv run run_tools.py refund
```

### 기대 출력 예시
```text
[user] ORD-1001 50000원 환불해줘
   tool call (대기): request_refund {'amount': 50000, 'order_id': 'ORD-1001'}
   final: ORD-1001번에 대한 환불 요청(티켓: TICKET-0001)이 접수되어 관리자 승인 대기 중입니다.
[승인 주입] TICKET-0001
   tool resp: request_refund -> {'status': 'approved', 'processed_at': '...'}
   final: 고객님, ORD-1001번 50,000원에 대한 환불이 승인 완료되었습니다.
```


