# memory_layers_agent — 이중 계층 메모리(Session 단기 vs Memory 장기) 에이전트

`memory_layers_agent`는 Google ADK의 **이중 계층 메모리(Dual-Layer Memory)** 아키텍처를 실습하기 위한 에이전트입니다.
대화의 임시 상태를 다루는 **Session Service(단기)**와 세션을 넘어 영속적인 사실과 지식을 유지하는 **Memory Service(장기)**를 결합하여 사용자 맞춤형 대화를 수행합니다.

> **관련 강의노트**: Part 2 · 02. Google ADK 아키텍처 (슬라이드 25)

---

## 1. 이중 계층 메모리 비교 매트릭스

| 비교 항목 | Session Service (단기) | Memory Service (장기) |
|---|---|---|
| **저장 범위** | 활성 대화 스레드 및 세션 임시 상태 | 세션을 넘어서는 영속적인 사용자 사실·선호·지식 |
| **저장 데이터** | 메시지 이력, 도구 호출 결과, State 변수 | 정리·추출된 사용자 프로필, 과거 사건 기록 |
| **생명주기** | 대화 스레드 종료 시 소멸 (또는 세션 DB에 보존) | 세션 간 영구 보존 |
| **구현체** | `InMemorySessionService`, `DatabaseSessionService`, `VertexAiSessionService` | `InMemoryMemoryService`, `VertexAiMemoryBankService` |
| **에이전트 접근 방식** | 이벤트 이력 자동 주입, `{key}` 지시문 템플릿, `tool_context.state` | `preload_memory`(매 턴 자동 검색), `load_memory`(능동 검색 도구) |

---

## 2. 세션 State 변수 접두사(Prefix) 규칙

ADK의 Session State는 키 접두사에 따라 공유 및 저장 범위가 엄격히 구분됩니다:

* **`user:<key>`** (예: `user:name`):
  * 동일 사용자(`user_id`)의 **모든 세션 간에 자동 공유**됩니다.
  * 프로필 정보나 사용자 고유 설정 저장에 적합합니다.
* **접두사 없음** (예: `trip`):
  * 해당 대화 세션(`session_id`) 내부에서만 유효합니다. 새 세션이 시작되면 초기화됩니다.
* **`app:<key>`** (예: `app:notice`):
  * 애플리케이션(`app_name`) 전역에서 모든 세션이 공유하는 전역 설정값입니다.
* **`temp:<key>`** (예: `temp:raw`):
  * 단일 호출 턴(Turn) 동안만 임시로 사용되며, 세션 저장소에 영구 기록되지 않습니다.

---

## 3. 에이전트 동작 원리 및 도구 구성

`memory_layers_agent`는 지시문(Instruction)과 도구를 통해 두 메모리 계층을 모두 활용합니다:

```text
               ┌────────────────────────────────────────────────────────┐
               │                  memory_layers_agent                   │
               └────────────────────────────────────────────────────────┘
                       │                                        │
           [단기 State 주입]                               [장기 Memory 검색]
          {user:name?}, {trip?}                     preload_memory / load_memory
                       │                                        │
                       ▼                                        ▼
    ┌─────────────────────────────────────┐  ┌────────────────────────────────────┐
    │       Session Service (단기)        │  │       Memory Service (장기)        │
    │  - user:name: 세션 간 유지          │  │  - add_session_to_memory로 축적   │
    │  - trip: 이번 세션에만 유효         │  │  - "매운", "부산" 등 키워드 검색  │
    └─────────────────────────────────────┘  └────────────────────────────────────┘
```

### ① 지시문(Instruction) 템플릿
```python
instruction="""
너는 개인 비서다.
[단기: 이번 세션 State]
  사용자 이름: {user:name?}
  이번 세션의 계획: {trip?}
규칙
...
"""
```
* `{user:name?}`: 세션 State에 `user:name`이 있으면 주입하고, 없으면 빈 문자열로 처리합니다.
* `{trip?}`: 이번 세션에 저장된 계획 정보를 프롬프트에 자동으로 주입합니다.

### ② 제공 도구 (Tools)
1. **`save_profile(name, tool_context)`**:
   * `tool_context.state["user:name"] = name`
   * 사용자 이름을 영속적인 `user:` 스코프 State로 저장합니다.
2. **`save_trip(trip, tool_context)`**:
   * `tool_context.state["trip"] = trip`
   * 출장이나 여행 일정을 현재 세션 스코프 State로 저장합니다.
3. **`preload_memory`**:
   * 매 턴 사용자 질문에 포함된 단어를 기준으로 Memory Service를 자동 사전 검색하여 프롬프트에 컨텍스트로 제공합니다.
4. **`load_memory`**:
   * 에이전트가 답변 중 과거 기억(음식 취향, 이전 대화 내용 등)이 추가로 필요할 때 능동적으로 장기 기억을 검색합니다.

---

## 4. 파일 구성

```text
part02_architecture/memory_layers_agent/
├── __init__.py           # agent 모듈 노출
├── agent.py              # root_agent, 도구(save_profile, save_trip), 메모리 도구 등록
└── README-KR.md          # 현재 설명서 문서
```

---

## 5. 실행 및 테스트 방법

상위 폴더인 `part02_architecture`에서 실행합니다:

```bash
cd part02_architecture

# 1) 메모리 계층 구조 비교 스크립트 실행 (오프라인 모드: LLM 없이 서비스 구조 확인)
uv run run_memory_layers.py offline

# 2) LLM 연동 테스트 (세션 1 저장 → 세션 2에서 장기 기억 인출 확인, Gemini 키 필요)
uv run run_memory_layers.py llm

# 3) 전체 실행 (기본값)
uv run run_memory_layers.py all

# 4) 터미널 대화형 실행
adk run memory_layers_agent

# 5) 웹 개발 UI 실행
adk web --port 8008
```

---

## 6. 시나리오 동작 예시

### [세션 1] 프로필과 단기 계획 및 취향 전달
* **User**: "안녕, 나는 김철수야. 매운 음식을 못 먹고, 다음 주 화요일에 부산 출장이 있어."
* **에이전트 동작**:
  1. `save_profile(name="김철수")` 호출 → `state["user:name"] = "김철수"` 저장
  2. `save_trip(trip="다음 주 화요일 부산 출장")` 호출 → `state["trip"] = "다음 주 화요일 부산 출장"` 저장
  3. 세션 종료 시 세션 대화 내용 전체가 `add_session_to_memory`를 통해 장기 기억으로 이관

### [세션 2] 새 대화 시작 (새 세션 ID)
* **상태**:
  * `trip` 변수는 이전 세션과 함께 초기화되어 존재하지 않음.
  * `user:name`은 사용자 스코프이므로 유지됨.
* **User**: "내 이름이 뭐였지? 그리고 이번 부산 출장 때 먹을 저녁 메뉴 하나만 추천해줘."
* **에이전트 동작**:
  1. 지시문 템플릿 `{user:name?}`을 통해 이름 "김철수"는 세션 State에서 즉시 인식.
  2. `preload_memory` 및 `load_memory("매운")` 검색을 통해 "매운 음식을 못 먹는다"는 과거 취향을 장기 기억에서 회상.
  3. **최종 응답**: "김철수님, 매운 음식을 피하셔야 하므로 맵지 않고 담백한 부산 돼지국밥이나 생선구이를 추천합니다."

