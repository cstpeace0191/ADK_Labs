# openapi_agent — OpenAPI 사양 기반 REST API 연동 에이전트

사내 REST API 명세서(`hr_api.yaml`)를 읽어와 별도의 함수 코드 작성 없이 각 엔드포인트를 에이전트의 도구로 자동 변환하는 실습입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent` (`hr_bot`)
- **OpenAPI 명세 (`hr_api.yaml`)**:
  - `operationId: get_leave_balance` → 에이전트 도구 `get_leave_balance`로 자동 등록
  - `operationId: list_holidays` → 에이전트 도구 `list_holidays`로 자동 등록
- **동적 인증 헤더 주입**:
  ```python
  hr_tools = OpenAPIToolset(
      spec_str=spec,
      spec_str_type="yaml",
      header_provider=lambda ctx: {"X-API-Key": os.getenv("HR_API_KEY", "demo-hr-key")},
  )
  ```
  API 키를 하드코딩하지 않고 환경 변수 및 동적 람다 함수를 통해 요청 헤더에 안전하게 주입합니다.

---

## 2. 실행 방법

`part06_tools` 폴더에서 진행하며, 2개의 터미널이 필요합니다:

```bash
cd part06_tools

# 터미널 1: HR 목업 서버 기동 (localhost:8000)
uv run openapi_agent/hr_mock_server.py

# 터미널 2: 도구 호출 테스트
uv run run_tools.py openapi
```

### 질의 예시
```text
User: 철수의 휴가 며칠 남았어?
Agent: [HR API get_leave_balance 호출]
Agent: 철수 님의 잔여 연차는 12일입니다.
```


