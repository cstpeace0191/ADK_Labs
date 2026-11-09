# analyst_agent — AgentTool 기반 분석가 에이전트

Gemini의 내장 전용 기능(`google_search`, `BuiltInCodeExecutor`)을 가진 독립 에이전트들을 `AgentTool`로 감싸, 상위 부모 에이전트가 일반 함수처럼 호출할 수 있도록 구성한 패턴입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent` (`analyst`)
- **구조도**:
  ```
                 [analyst (root_agent)]
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  [AgentTool]        [AgentTool]       [Function Tools]
  searcher           calculator        list_products, add_to_cart
  (google_search)    (코드 실행기)
  ```
- **AgentTool의 필요성**:
  - `google_search`나 `BuiltInCodeExecutor`는 Gemini 고유 기능으로 다른 일반 커스텀 도구와 하나의 에이전트에서 혼용하기 까다롭습니다.
  - 이를 각각 전담 서브 에이전트로 분리하고 `AgentTool(agent=...)`로 래핑하여 부모 에이전트에게 단일 도구 인터페이스로 제공합니다.

---

## 2. 실행 방법

`part06_tools` 폴더에서 실행합니다:

```bash
cd part06_tools
uv run run_tools.py analyst
```

> ⚠ **참고**: `google_search` 기능은 무료 API 키에서 분당 호출 한도(429)로 차단될 수 있습니다. 계산기(`calculator`) 코드 실행은 정상 동작합니다.


