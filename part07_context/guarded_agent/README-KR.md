# guarded_agent — Callback 가드레일 및 감사 로깅 에이전트

LLM 호출 전후 및 도구 실행 전후에 개입하여 보안 정책을 강제하는 콜백(Callback)과 플러그인(Plugin)을 실습하는 에이전트입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **구현된 가드레일**:
  1. **`before_model_callback` (`guard`)**:
     - 사용자 입력에 "주민등록번호", "비밀번호" 등 금칙어가 포함되어 있으면 LLM을 호출하지 않고 즉시 차단 메시지를 반환합니다 (🟢 토큰 및 API 비용 0).
  2. **`before_tool_callback` (`check_args`)**:
     - `add_to_cart` 도구 호출 시 수량이 10개를 초과하면 도구 함수를 실행하지 않고 에러 반환.
  3. **`AuditPlugin`**:
     - `BasePlugin`을 상속하여 모든 LLM 요청 프롬프트와 모델 응답을 감사 로그로 기록.

---

## 2. 실행 방법

`part07_context` 폴더에서 실행합니다:

```bash
cd part07_context
uv run run_callbacks.py
```

### 기대 출력 예시
```text
[user] 주민등록번호 알려줄게: 900101-1234567
  → 차단: 민감정보는 처리할 수 없습니다. (LLM 호출 차단됨)

[user] 마우스 99개 담아줘
  → 도구 에러: 최대 10개 (도구 함수 미실행)
```


