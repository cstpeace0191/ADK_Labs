# appendixA_python_for_adk — 부록 A. Python for ADK 실습

> 강의노트 `10-12주차강의노트(Google ADK Agent Programming)_20261111f.pptx`의 **부록 A (슬라이드 163–198)** 와 짝을 이룬다.
> ADK 코드를 읽고 확장하는 데 필요한 Python 기법(async/await, 이벤트 루프, 동시성 제어, 제너레이터,
> async with, 타입 힌트 · Pydantic, 상속 · 콜백 · 데코레이터)을 **직접 실행해서 확인**한다.

**모든 스크립트가 🟢 LLM 없이 실행된다** (Gemini 키 불필요). ADK가 등장하는 실습은 두 가지 방법으로 Runner의 실제 코드를 돌린다.

- **커스텀 에이전트**(`BaseAgent` 상속): 토큰 조각 · 이벤트를 직접 만들어 내는 에이전트 (A3 · A6 · A7)
- **대본대로 답하는 모델**(`_helpers.scripted_model`): `before_model_callback`이 정해진 응답을 돌려준다.
  부록 A6 콜백 슬라이드의 원리(값을 돌려주면 모델 호출을 건너뜀)를 이용해,
  LLM 없이도 function_call → 도구 실행 → function_response → 재호출 루프를 그대로 돌린다 (A5 · A6 · A7)

## 실행

`ADK_Labs/appendixA_python_for_adk` 폴더에서:

```bash
uv run run_all.py --quiet          # 7개 스크립트를 모두 실행하고 요약만 보기
uv run a1_async_basics.py order    # 항목 하나만 실행 (항목 없이 실행하면 all)
```

가상환경을 활성화했다면 `uv run` 대신 `python`으로 실행해도 된다.

## 슬라이드 ↔ 실습 지도

| 부록 (슬라이드) | 스크립트 · 항목 | 확인할 것 |
|---|---|---|
| **A1** 동기 vs 비동기 (165) · async/await (168) | `a1_async_basics.py sync` | 동기 0.9s vs 비동기 0.3s — 대기가 겹친다 |
| A1 await (169) | `a1_async_basics.py await` | `handle()`이 응답을 기다리는 동안 다른 코루틴이 돈다 |
| A1 await는 언제 멈추나 (170) | `a1_async_basics.py suspend` | `quick → quick → other 실행 → sleep(0) 이후` — 바로 끝나는 코루틴은 양보하지 않는다 |
| A1 await의 동작 구조 (171) | `a1_async_basics.py bytecode` | `GET_AWAITABLE → SEND → YIELD_VALUE → RESUME → … → STORE_FAST` |
| A1 이벤트 루프 (172–174) | `a1_async_basics.py loop` | `_ready`(call_soon · create_task) · `_scheduled`(call_later) 대기열 |
| A1 스케줄링 실험 (175) | `a1_async_basics.py order` | 슬라이드의 표와 같은 순서: call_soon → A·B·C 시작 → C 끝 → B 끝 → call_later → A 끝 |
| A1 asyncio 핵심 객체 (176) | `a1_async_basics.py objects` | `never awaited` 경고 · Task는 Future · TaskGroup 실패 시 나머지 취소 |
| A1 asyncio.run 동작 구조 (178) | `a1_async_basics.py run` | 실행 중 루프 안에서 `asyncio.run()` → RuntimeError, main 종료 시 남은 Task 취소 |
| **A2** Lock · Semaphore · Event (179) | `a2_concurrency.py lock` · `semaphore` · `event` | Lock 없으면 100번 더해도 1 · 동시 실행 최대 3 · '저장될 때까지 대기' 핸드셰이크 |
| A2 gather vs TaskGroup (180) | `a2_concurrency.py gather` · `taskgroup` | gather는 직접 cancel해야 정리됨 · TaskGroup은 자동 취소 + `except*` |
| A2 타임아웃 · contextvars (181) | `a2_concurrency.py timeout` · `contextvars` | 블록 바깥에서 TimeoutError · Task마다 다른 request_id |
| **A3** iterator · generator · yield (182–184) | `a3_generators.py iter` · `yield` · `agen` | StopIteration · yield에서 멈췄다 재개 · async generator가 생기는 즉시 내보냄 |
| A3 async generator와 스트리밍 (185) | `a3_generators.py stream` | partial 조각이 하나씩 화면에 붙고, **세션에는 최종 응답만 저장**된다 |
| **A4** async for · async with (186) | `a4_context_managers.py aiter` · `awith` · `runner` | 예외가 나도 `__aexit__` 실행 · `async with Runner(...)`가 끝나면 도구 세트 · 플러그인 close |
| A4 contextlib (187) | `a4_context_managers.py acm` · `aclosing` | aclosing이 없으면 break 뒤 finally가 늦게 실행된다 |
| **A5** 타입 힌트 = 도구 스키마 (188, 본문 77) | `a5_types_pydantic.py schema` | 실제 선언 JSON: 기본값 있는 `unit`은 required에서 빠짐 |
| A5 Pydantic 도구 입력 (189) | `a5_types_pydantic.py pydantic` · `validate` | `$defs.Order`의 `minimum: 1` · dict → Order 변환 · 잘못된 인자 처리 (아래 '버전 차이') |
| A5 고급 typing (190) | `a5_types_pydantic.py typing` | `BeforeModelCallback` 타입 별칭 해석 |
| **A6** Agent는 Pydantic 모델 (191) | `a6_extend_adk.py model` | 공백 이름 · 오타 인자 `instructon` · 이름 `user` → ValidationError, `clone()` |
| A6 커스텀 에이전트 (192) | `a6_extend_adk.py custom` | writer/critic을 돌리다 state `approved`가 되면 멈춤 |
| A6 콜백 (193, 본문 88–89) | `a6_extend_adk.py callback` | 플러그인 → sync → async 순, 처음 값을 돌려준 콜백에서 멈춤 |
| A6 데코레이터 · inspect (194, 본문 77) | `a6_extend_adk.py decorator` | wraps 없으면 이름이 `wrapper`가 되고 설명 · 인자가 사라짐 · ToolContext 주입 |
| **A7** run_async 실제 실행 본체 (196, 본문 25) | `a7_runner.py run_async` | 호출자가 처리를 끝내야 다음 이벤트가 생성된다 |
| A7 run()은 하나씩 (197, 본문 26) | `a7_runner.py run` | 백그라운드가 앞서 생성, 호출자는 첫 이벤트를 바로 받고 나머지는 큐에서 꺼냄 |
| 병렬 도구 호출 (본문 78 · 부록 180) | `a7_runner.py parallel` | 한 응답의 도구 2개가 같은 시각에 시작해 함께 끝난다 |

## 폴더 구조

```text
appendixA_python_for_adk/
├── _path.py               # 실습 루트를 import 경로에 넣고 .env를 읽는다 (다른 Part와 같은 방식)
├── _helpers.py            # section · Clock · scripted_model(대본 모델) · run_turn(Runner 한 턴)
├── a1_async_basics.py     # A1 비동기 · asyncio (165–178)
├── a2_concurrency.py      # A2 동시성 제어 (179–181)
├── a3_generators.py       # A3 제너레이터 · 스트리밍 (182–185)
├── a4_context_managers.py # A4 async for · async with (186–187)
├── a5_types_pydantic.py   # A5 타입 힌트 · Pydantic (188–190)
├── a6_extend_adk.py       # A6 객체 모델 · 확장 (191–194)
├── a7_runner.py           # A7 ADK Runner (195–197)
└── run_all.py             # 전체 실행 · 요약
```

## 버전 차이 (부록 슬라이드는 google-adk 2.6.3, 이 실습 venv는 2.14.0)

부록 A의 설명은 google-adk 2.6.3 소스로 확인했고, 이 실습은 `ADK_Labs/.venv`의 **google-adk 2.14.0 · Python 3.12**에서 실행해 확인했다.
슬라이드의 내용은 2.14.0에서도 그대로 성립하며, 다음이 더해지거나 바뀌었다.

| 항목 | 2.6.3 (슬라이드) | 2.14.0 (실습 결과) |
|---|---|---|
| Pydantic 인자 변환 실패 (189) | 경고만 남기고 원래 dict를 함수에 넘김 | 기본 동작은 같다. 실험 기능 `FUNCTION_TOOL_ARG_VALIDATION`을 켜면(`ADK_ENABLE_FUNCTION_TOOL_ARG_VALIDATION=1`) 함수를 실행하지 않고 오류를 LLM에 돌려준다 (`a5 validate` ②) |
| 콜백 첫 인자 타입 (190) | `CallbackContext` | `Context` (쓰는 법은 같다) |
| `Runner.run()` (197) | 큐 + 백그라운드 스레드 + `asyncio.run()` | 같은 구조에 더해, 백그라운드 예외를 호출자에게 다시 던지고 호출자가 중간에 멈추면 실행을 취소한다 |
| `await` 바이트코드 (171) | Python 3.11 기준 | Python 3.12는 `END_SEND` 등이 더 보인다 (`a1 bytecode`) |
