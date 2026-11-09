# state_agent — 접두사 스코프 기반 State 관리 에이전트

`user:`, `app:`, `temp:` 접두사에 따른 상태의 유효 범위와 `DatabaseSessionService(SQLite)`를 통한 영속적 상태 보존을 검증하는 에이전트입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **도구 연동**:
  - `set_name`: `tool_context.state['user:name'] = name` 형태로 사용자 정보 저장
  - `record_visit`: 세션별 방문 횟수(`visits`) 및 임시 데이터(`temp:last_tool`) 갱신
- **영속성 검증**:
  - 세션 1에서 사용자의 이름을 저장하면 SQLite DB(`sessions.db`)에 커밋됩니다.
  - 동일한 `user_id`를 가진 새로운 세션 2를 생성했을 때 `user:name`은 그대로 보존되어 인사하고, 세션 범위 변수인 `visits`는 0부터 다시 시작됩니다.

---

## 2. 실행 방법

`part07_context` 폴더에서 실행합니다:

```bash
cd part07_context
uv run run_state_sessions.py
```


