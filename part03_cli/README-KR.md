# part03_cli — 개발 환경과 adk CLI

`part03_cli` 폴더(= 에이전트들의 상위 폴더)에서 실행한다. 강의노트 **Part 3 · 03. 개발 환경과 CLI**(슬라이드 26–43)와 짝을 이룬다.

```text
part03_cli/
├── my_agent/
│   ├── __init__.py       # from . import agent
│   └── agent.py          # root_agent = Agent(...)   ← 개발자가 쓰는 것은 이것뿐 (adk 사용 시)
├── run_direct_runner.py  # 🔑 직접 Runner 코드: 등록 → 실행 → 이벤트 소비 (슬라이드 27–29 · 33)
├── adk_internals.py      # 🟢/🔑 adk 가 대신 해 주는 5단계 재현 (슬라이드 30–32)
└── api_client.py         # 🔑 adk api_server 의 /run · /run_sse 호출 (슬라이드 37)
```

`.env`는 실습 루트(`ADK_Labs/.env`) 하나만 두면 된다. adk가 에이전트 폴더에서 상위로 올라가며 찾는다.

## 1. 같은 에이전트, 두 가지 실행 방식 (슬라이드 27–33)

ADK 응용 SW의 뼈대는 `Runner`다. 같은 `my_agent/agent.py`를 두 방식으로 실행해 비교한다.

| 방식 | 개발자가 쓰는 것 | 실습 |
|---|---|---|
| 직접 Runner 코드 | root_agent + Runner · 서비스 · 입출력 코드 | `run_direct_runner.py` |
| adk CLI | root_agent(agent.py)만 | `adk run my_agent` · `adk_internals.py` |

### ① 직접 Runner 코드: 등록 → 실행 → 이벤트 소비 (🔑)

```bash
uv run run_direct_runner.py "부산 날씨 알려줘"
```

```text
① 등록   Runner(agent=weather_agent, session_service=InMemorySessionService)
② 실행   run_async(new_message='부산 날씨 알려줘')
   [Event 1] 모델 호출 → function_call get_weather({'city': '부산'})   (모델은 요청만)
   [Event 2] 도구 실행 → function_response get_weather: {'status': 'success', 'report': '흐림, 20°C'}   (Runner 가 실행)
③ 소비   최종 응답(Event 3): 부산의 현재 날씨는 흐리고 기온은 20°C입니다.
```

`run_async()` 한 번이 agent loop 한 바퀴다(슬라이드 29): 모델이 function_call을 "요청"하면 Runner가 도구를 실행하고 결과로 모델을 다시 부른다.

### ② adk 가 대신 해 주는 일 (🟢 키 없이 ①~④, 🔑 ⑤)

`adk run my_agent`가 내부에서 하는 5단계를 ADK 자신의 코드(`AgentLoader`, `load_dotenv_for_agent`, `create_*_service_from_options`)로 그대로 재현한다.

```bash
uv run adk_internals.py                    # ①~④ (LLM 호출 없음)
uv run adk_internals.py --in_memory         # adk run --in_memory 와 같은 서비스 선택
uv run adk_internals.py --ask "서울 날씨?"   # ⑤ 까지: adk run 의 한 턴
```

```text
① 찾기       AgentLoader → LlmAgent name='weather_agent' (from my_agent/agent.py)
② .env 로드   GOOGLE_API_KEY 설정됨=True · ADK_MODEL=gemini-3.5-flash-lite
③ 서비스 생성  session=PerAgentDatabaseSessionService → my_agent/.adk/session.db (SQLite, 첫 세션 때 생성)
              artifact=PerAgentFileArtifactService · memory=InMemoryMemoryService
④ Runner 생성  Runner(app='my_agent', root_agent='weather_agent')
⑤ 입구 제공   adk run 이면 여기서 input('[user]: ') 루프 → runner.run_async()
```

- **기본 세션 저장소는 InMemory가 아니다.** 플래그가 없으면 에이전트 폴더의 `.adk/session.db`(SQLite)에 저장된다.
  `--in_memory`를 주거나 Cloud Run·Kubernetes에서 실행되면 InMemory로 바뀐다. 운영에서는 `--session_service_uri`로 지정한다.
- `adk web`·`adk api_server`도 같은 서비스·Runner를 만들고, 차이는 ⑤ 입구(HTTP)뿐이다(슬라이드 32).
- `google.adk.cli.utils`는 ADK 내부 API라 버전마다 바뀔 수 있다(2.6.3 기준 학습용 재현).
- `adk run`·`adk_internals.py`를 실행하면 `my_agent/.adk/` 폴더가 생긴다. 지워도 된다.

## 2. agents-cli (슬라이드 38–43, 상세는 Part 12 슬라이드 125–137)

agents-cli 소개 · adk와의 비교 · 명령 지도 · 프로젝트 구조 · 동작 구조 실습은 [`part12_agents_cli/`](../part12_agents_cli/README-KR.md)에 있다.

## 3. adk 명령 (슬라이드 34–37)

| 명령 | 하는 일 |
|---|---|
| `adk create my_agent2` | agent.py · \_\_init\_\_.py · .env 골격 생성 |
| `adk run my_agent` | 터미널 REPL (예: `서울 날씨 알려줘`) |
| `adk run --save_session --session_id s1 my_agent` | 종료 시 `my_agent/s1.session.json` 저장 → eval 데이터로 재활용 |
| `adk run --resume my_agent/s1.session.json my_agent` | 저장한 대화를 이어서 진행 |
| `adk run --replay queries.json my_agent` | `{"state": {...}, "queries": [...]}` 입력 파일을 사람 입력 없이 실행 (세션 파일이 아니다) |
| `adk web --port 8000` | 개발 UI: http://localhost:8000 (Events · Trace · State · Graph 탭) |
| `adk api_server --port 8000 --session_service_uri="sqlite:///sessions.db"` | 헤드리스 REST/SSE 서버 |

플래그는 버전마다 다를 수 있으니 `adk run --help`로 확인한다.

## api_server 호출

```bash
adk api_server --port 8000
```

다른 터미널에서:

```bash
uv run api_client.py
```

curl로 직접 호출할 때:

```bash
curl -X POST localhost:8000/apps/my_agent/users/u1/sessions/s1
```

```bash
curl -X POST localhost:8000/run -H "Content-Type: application/json" -d "{\"app_name\":\"my_agent\",\"user_id\":\"u1\",\"session_id\":\"s1\",\"new_message\":{\"role\":\"user\",\"parts\":[{\"text\":\"서울 날씨?\"}]}}"
```

