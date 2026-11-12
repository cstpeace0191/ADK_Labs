# part07_context — Context, State, Memory 및 Guardrails

> 강의노트 **Part 7 · 07. Session · State · Memory · Callback** (슬라이드 83–89)과 짝을 이룬다.

대화의 상태를 관리하는 **State 접두사 스코프**, **세션 영속성(SQLite DatabaseSessionService)**, 장기 기억을 위한 **MemoryService**, 그리고 보안 및 모니터링을 위한 **Callbacks & Plugin 가드레일**을 다룹니다.

---

## 1. 폴더 구조 및 서브 에이전트

```text
part07_context/
├── state_agent/             # State 범위(user:, app:, 세션) 및 SQLite 영속성
├── memory_agent/            # InMemoryMemoryService 기반 과거 세션 기억 회상
├── guarded_agent/           # before_model, before_tool 콜백 기반 가드레일
├── audit_plugin.py          # 모든 LLM 요청/응답을 가로채는 BasePlugin 구현체
├── run_state_sessions.py    # 🔑 SQLite 기반 사용자 상태 유지 실습 러너
├── run_memory.py            # 🔑 장기 기억(Memory) 저장 및 검색 실습 러너
├── run_callbacks.py         # 🟢/🔑 콜백 가드레일 및 AuditPlugin 동작 러너
└── README-KR.md                # 현재 문서
```

---

## 2. 핵심 개념 요약

### ① State 접두사 스코프 규칙
- `user:name`: 사용자 레벨 상태 (동일 사용자의 새 세션에서도 영구 유지)
- `app:notice`: 앱 전역 공통 상태 (모든 사용자가 공유)
- `temp:cached`: 메모리 임시 상태 (세션 DB에 영속화되지 않음)
- `visits`: 세션 레벨 상태 (해당 대화 세션 종료 시 소멸)

### ② Callbacks 동작 규칙
- `before_model_callback`: LLM 호출 직전 요청 검사. `LlmResponse`를 반환하면 LLM 호출을 건너뛰고 해당 응답을 즉시 반환(민감 정보 차단 가드레일).
- `before_tool_callback`: 도구 실행 직전 인자 검증. `dict`를 반환하면 실제 도구 함수를 실행하지 않고 해당 에러 결과를 주입(수량 제한 가드레일).

---

## 3. 실행 방법

모든 명령은 `part07_context` 폴더에서 실행합니다:

```bash
cd part07_context

# 1. State 스코프 및 SQLite 세션 영속성 테스트 (🔑 Gemini 키 필요)
uv run run_state_sessions.py

# 2. 장기 기억(Memory) 저장 및 회상 테스트 (🔑 Gemini 키 필요)
uv run run_memory.py

# 3. 콜백 가드레일 및 플러그인 로깅 테스트 (차단 시 🟢 오프라인)
uv run run_callbacks.py
```



