# part02_architecture — Google ADK 아키텍처 및 이벤트 생명주기

> 강의노트 **Part 2 · 02. Google ADK 아키텍처** (슬라이드 16–25)와 짝을 이룬다.

Google ADK(Agent Development Kit)의 핵심 실행 아키텍처인 **Runner**, **Agent**, **Event Stream**의 생명주기를 이해하고 관찰하는 실습입니다.
또한 **이중 계층 메모리**(Session 단기 vs Memory 장기, 강의노트 슬라이드 25)를 서비스 API와 에이전트로 직접 확인합니다.

---

## 1. 폴더 구조

```text
part02_architecture/
├── chat_time_weather_agent/     # 시간·날씨(geocode 연동) 및 일반 질문 답변 에이전트
│   ├── __init__.py              # from . import agent
│   ├── agent.py                 # root_agent 정의 (geocode, get_current_time, get_weather 연동)
│   └── README-KR.md             # chat_time_weather_agent 상세 설명서
├── memory_layers_agent/         # 이중 계층 메모리 에이전트 (State 템플릿 + preload/load_memory)
│   ├── __init__.py
│   ├── agent.py                 # save_profile(user:) · save_trip(세션) · preload_memory · load_memory
│   └── README-KR.md             # memory_layers_agent 상세 설명서
├── run_events.py                # 🔑 LLM 연동 Event 생명주기 관찰 러너
├── run_workflow_events.py       # 🟢 LLM 없이 실행 가능한 Workflow Event 필드 관찰 러너
├── run_memory_layers.py         # 🟢/🔑 Session(단기) vs Memory(장기) 비교 러너 (슬라이드 25)
└── README-KR.md                    # 현재 문서
```

---

## 2. 핵심 아키텍처 개념

```
[사용자 요청] 
      │
      ▼
   Runner ──(SessionService)── 세션 및 상태 관리
      │
      ├─①─▶ Agent (LLM / Prompt) ──▶ Gemini API
      │                                  │ (Function Call 요청)
      │                                  ▼
      ├─②◀─ Runner가 도구(Tool) 직접 실행 후 응답 주입
      │
      ▼
[최종 응답 Event 전달]
```

- 모든 상호작용은 **Event 스트림**으로 발행되며, 각 이벤트는 `author`, `function_calls`, `function_responses`, `actions(state_delta, route)`, `content` 등의 메타데이터를 포함합니다.

---

## 3. 실행 방법

모든 명령은 실습 루트 또는 `part02_architecture/` 폴더에서 실행합니다.

### ① 대화형 인터페이스 (`adk web` / `adk run`)
```bash
# part02_architecture 폴더로 이동
cd part02_architecture

# 웹 개발 UI 실행 (http://localhost:8008)
adk web --port 8008

# 또는 터미널 CLI 대화형 실행
adk run chat_time_weather_agent
```

### ② 스크립트 실행 (Event 스트림 분석)

#### 1) LLM 연동 Event 생명주기 관찰 (🔑 Gemini 키 필요)
모델이 도구 호출을 생성하고, Runner가 도구를 대행 실행하여 최종 응답을 합성하는 3단계 과정을 콘솔에서 확인합니다:
```bash
uv run run_events.py
```
**기대 출력**:
```text
--- Event author=root_agent
  ① 모델이 도구 호출을 '요청': get_current_time {'city': '서울'}
--- Event author=root_agent
  ② Runner가 도구를 실행한 결과: {'status': 'success', 'city': '서울', 'time': '10:30 AM'}
--- Event author=root_agent
  ③ 최종 응답: 현재 서울의 시간은 오전 10시 30분입니다.
```

#### 2) Workflow Event 필드 관찰 (🟢 LLM 없이 실행 가능)
ADK 2.0의 `Event` 구조체 필드(`node_info`, `route`, `output`, `message`)가 노드 간에 전파되는 과정을 확인합니다:
```bash
uv run run_workflow_events.py
```
**기대 출력**:
```text
[user] hello ADK
  node=event_demo@1/classify@1      route=LONG   output={'text': 'hello ADK'}  message=None
  node=event_demo@1/long_msg@1      route=None   output=None                   message=긴 입력: hello ADK

[user] hi
  node=event_demo@1/classify@1      route=SHORT  output={'text': 'hi'}         message=None
  node=event_demo@1/short_msg@1     route=None   output=None                   message=짧은 입력: hi
```

#### 3) 이중 계층 메모리: Session(단기) vs Memory(장기) (🟢 / 🔑, 슬라이드 25)

강의노트 표의 다섯 차원(저장 범위 · 데이터 · 생명주기 · 구현 · 읽는 방법)을 코드로 하나씩 확인합니다.

| 차원 | Session Service (단기) | Memory Service (장기) | 실습에서 보는 곳 |
|---|---|---|---|
| 저장 범위 | 활성 대화 스레드와 임시 상태 | 세션을 넘는 영속 사실·지식 | [A]③ 새 세션에는 이력 없음 · [B]③ 다른 사용자는 검색 불가 |
| 데이터 | 메시지 이력, 도구 호출, State 변수 | 정리된 사용자 선호·기록 | [A]①② 이벤트·State · [B]② `search_memory` |
| 생명주기 | 대화 스레드 종료와 함께 소멸 | 세션 간 영구 보존 | [A]④ InMemory 소멸 vs SQLite 보존 · [C] 세션 2에서 회상 |
| 구현 | InMemory · Database · VertexAiSessionService | InMemoryMemoryService · VertexAiMemoryBankService | `InMemorySessionService`, `DatabaseSessionService`, `InMemoryMemoryService` |
| 읽는 방법 | event 이력, `{key}` 템플릿, `tool_context.state` | `load_memory` / `preload_memory` 도구 | `memory_layers_agent`: `{user:name?}` · `{trip?}` 템플릿, `save_*` 도구, `preload_memory` · `load_memory` |

```bash
uv run run_memory_layers.py offline   # 🟢 키 없이: [A] Session, [B] Memory 를 서비스 API로 확인
uv run run_memory_layers.py llm       # 🔑 Gemini 키: [C] 에이전트가 두 계층에서 기억을 꺼낸다
uv run run_memory_layers.py           # 둘 다
```

**기대 출력 (offline 요약)**:
```text
[A] Session Service (단기)
② 데이터: State 변수 (접두사로 범위 결정)
   - trip       = 다음 주 화요일 부산 출장
   - app:notice = 금요일 휴강
   - user:name  = 김철수
   → temp:raw 는 기록되지 않는다: True
③ 저장 범위: 같은 사용자의 '새' 세션 2
   - 이벤트 0개 (대화 이력은 세션 1에만)
   - user:name = 김철수  (user: 접두사는 사용자 범위)
   - trip      = None  (접두사 없음 = 세션 1에서만)
④ 생명주기 · 구현: 서비스를 새로 만들면(= 프로세스 재시작)
   - InMemorySessionService  → None (소멸)
   - DatabaseSessionService  → 이벤트 2개, user:name=김철수 (보존)
[B] Memory Service (장기)
② search_memory('부산') → 1건
② search_memory('제주') → 0건
② search_memory('부산에서') → 0건
   → InMemory 는 '단어가 그대로 같은지'만 본다. '부산에서'(조사 붙음)로는 '부산'을 못 찾는다
```

**기대 출력 (llm 요약)**:
```text
=== 세션 1
  [tool call] save_profile({"name": "김철수"})
  [tool call] save_trip({"trip": "다음 주 화요일 부산 출장"})
→ 세션 1을 Memory 에 저장 (add_session_to_memory)
=== 세션 2: 새 대화
[user] 내 이름이 뭐였지? 그리고 이번 부산 출장 때 먹을 저녁 메뉴 하나만 추천해줘.
  [memory_layers_agent] 성함은 김철수님이십니다. 매운 음식을 못 드신다고 하셨으니 … 돼지국밥을 추천해 드립니다.
세션2 state: {'user:name': '김철수'}
```
- 이름은 **단기 계층**(`user:` State가 새 세션에도 남음, instruction의 `{user:name?}` 템플릿)에서 나옵니다.
- "매운 음식을 못 먹음"은 세션 2 State에 없습니다. **장기 계층**에서 `preload_memory`가 사용자 문장으로 검색해 프롬프트에 넣어 준 것입니다(도구 호출 이벤트 없이 동작).

**주의**
- `InMemoryMemoryService`는 단어 일치 검색입니다. 한국어는 조사가 붙으면("부산에서", "음식을") 일치하지 않으므로, 에이전트 지시문에 "load_memory 검색어는 조사 없는 핵심 단어"를 적어 두었습니다.
- 운영에서는 `VertexAiMemoryBankService`(사실 자동 추출·병합, 의미 검색)와 `DatabaseSessionService`/`VertexAiSessionService`를 씁니다. Cloud Run에서 세션 URI를 지정하지 않으면 인스턴스가 재활용될 때 대화가 사라집니다.
- offline 모드는 Runner가 내부에서 하는 기록(`append_event`)을 직접 호출해 저장 구조를 보여 줍니다. 에이전트·워크플로우 코드에서는 세션에 이벤트를 직접 append 하지 않습니다.
- State 접두사와 Memory를 더 깊게 다루는 실습은 `part07_context/`(`run_state_sessions.py`, `run_memory.py`)에 있습니다.

