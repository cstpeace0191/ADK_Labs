"""강의노트 Part 2 슬라이드 25: 이중 계층 메모리 — Session(단기) vs Memory(장기) 를 직접 확인한다.

실행:
  python run_memory_layers.py offline   🟢 LLM 없이: 저장 범위 · 데이터 · 생명주기 · 구현 · 읽는 방법을 서비스 API 로 확인
  python run_memory_layers.py llm       🔑 Gemini 키: 에이전트가 세션 State 와 load_memory/preload_memory 로 기억을 꺼낸다
  python run_memory_layers.py all       둘 다 (기본)

offline 은 Runner 가 내부에서 하는 일(append_event 로 이벤트 기록)을 직접 호출해 저장 구조를 보여 준다.
에이전트·워크플로우 코드에서는 세션에 이벤트를 직접 append 하지 않는다 (슬라이드 24 참고).
"""
import asyncio
import sys
import time
from pathlib import Path

import _path  # noqa: F401
from google.adk.events import Event, EventActions
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.genai import types

APP, USER = "memory_layers", "u1"
DB = Path(__file__).with_name("memory_layers.db")


def _user_turn(text: str) -> Event:
    return Event(author="user", invocation_id=f"inv-{time.time_ns()}",
                 content=types.Content(role="user", parts=[types.Part(text=text)]))


def _agent_turn(text: str, state_delta: dict | None = None) -> Event:
    return Event(author="assistant", invocation_id=f"inv-{time.time_ns()}",
                 content=types.Content(role="model", parts=[types.Part(text=text)]),
                 actions=EventActions(state_delta=state_delta or {}))


async def record_conversation(ss, session_id: str | None = None):
    """세션 1: 대화 한 번을 기록한다 (메시지 이력 + State 변경)."""
    s = await ss.create_session(app_name=APP, user_id=USER, session_id=session_id,
                                state={"app:notice": "금요일 휴강"})
    await ss.append_event(s, _user_turn("나는 김철수야. 매운 음식을 못 먹어. 다음 주 화요일에 부산 출장이 있어."))
    await ss.append_event(s, _agent_turn("기억해 둘게요, 김철수님.",
                                         {"user:name": "김철수", "trip": "다음 주 화요일 부산 출장",
                                          "temp:raw": "이번 호출에서만 쓰는 값"}))
    return await ss.get_session(app_name=APP, user_id=USER, session_id=s.id)


async def offline():
    print("=" * 70 + "\n[A] Session Service (단기)\n" + "=" * 70)
    ss = InMemorySessionService()
    s1 = await record_conversation(ss)
    print("① 데이터: 메시지 이력")
    for ev in s1.events:
        print(f"   - {ev.author:9}: {ev.content.parts[0].text}")
    print("② 데이터: State 변수 (접두사로 범위 결정)")
    for k, v in s1.state.items():
        print(f"   - {k:10} = {v}")
    print("   → temp:raw 는 기록되지 않는다:", "temp:raw" not in s1.state)

    s2 = await ss.create_session(app_name=APP, user_id=USER)
    print("③ 저장 범위: 같은 사용자의 '새' 세션 2")
    print(f"   - 이벤트 {len(s2.events)}개 (대화 이력은 세션 1에만)")
    print(f"   - user:name = {s2.state.get('user:name')}  (user: 접두사는 사용자 범위)")
    print(f"   - trip      = {s2.state.get('trip')}  (접두사 없음 = 세션 1에서만)")

    print("④ 생명주기 · 구현: 서비스를 새로 만들면(= 프로세스 재시작)")
    restarted = InMemorySessionService()
    print("   - InMemorySessionService  →",
          await restarted.get_session(app_name=APP, user_id=USER, session_id=s1.id), "(소멸)")
    DB.unlink(missing_ok=True)
    url = f"sqlite+aiosqlite:///{DB.as_posix()}"
    async with DatabaseSessionService(db_url=url) as db1:
        d1 = await record_conversation(db1, session_id="s-persist")
    async with DatabaseSessionService(db_url=url) as db2:  # 재시작 흉내: 새 인스턴스
        again = await db2.get_session(app_name=APP, user_id=USER, session_id="s-persist")
        print(f"   - DatabaseSessionService  → 이벤트 {len(again.events)}개, user:name={again.state.get('user:name')} (보존)")
    print("   - 운영(GCP 관리형): VertexAiSessionService (Agent Runtime)")

    print("\n" + "=" * 70 + "\n[B] Memory Service (장기)\n" + "=" * 70)
    memory = InMemoryMemoryService()
    await memory.add_session_to_memory(s1)  # 세션이 끝나면 장기 기억으로 옮긴다
    print("① add_session_to_memory(세션 1) → 세션을 넘는 영속 지식으로 저장")
    for q in ("부산", "매운", "제주", "부산에서"):
        res = await memory.search_memory(app_name=APP, user_id=USER, query=q)
        hits = [m.content.parts[0].text[:40] for m in res.memories]
        print(f"② search_memory('{q}') → {len(hits)}건 {hits}")
    print("   → InMemory 는 '단어가 그대로 같은지'만 본다. '부산에서'(조사 붙음)로는 '부산'을 못 찾는다")
    print("③ 다른 사용자는 볼 수 없다:",
          len((await memory.search_memory(app_name=APP, user_id="u2", query="부산")).memories), "건")
    print("④ 에이전트는 이 검색을 load_memory(필요할 때) · preload_memory(매 턴 자동) 도구로 쓴다")
    print("   운영: VertexAiMemoryBankService — 사실을 자동 추출·병합하고 의미 검색 (InMemory 는 단어 일치)")
    DB.unlink(missing_ok=True)


async def with_llm():
    from common.bootstrap import require_llm
    from common.runner_util import Session
    from memory_layers_agent.agent import root_agent
    require_llm()
    ss, memory = InMemorySessionService(), InMemoryMemoryService()

    print("\n" + "=" * 70 + "\n[C] 에이전트로 확인 (Gemini)\n" + "=" * 70)
    print("=== 세션 1: 사실을 알려준다 (단기 State 에 저장)")
    s1 = Session(root_agent, app_name=APP, user_id=USER, session_service=ss, memory_service=memory)
    await s1.send("안녕, 나는 김철수야. 매운 음식을 못 먹고, 다음 주 화요일에 부산 출장이 있어.")
    st1 = (await s1.get_session()).state
    print("세션1 state:", {k: v for k, v in st1.items() if not k.startswith("_")})
    await memory.add_session_to_memory(await s1.get_session())
    print("→ 세션 1을 Memory 에 저장 (add_session_to_memory)")

    print("\n=== 세션 2: 새 대화 — trip 은 없고 user:name 만 남는다. 나머지는 Memory 에서 꺼낸다")
    s2 = Session(root_agent, app_name=APP, user_id=USER, session_service=ss, memory_service=memory)
    # preload_memory 는 이 문장의 단어로 검색한다 → '부산'이 그대로 들어 있어야 InMemory 에서 찾힌다
    await s2.send("내 이름이 뭐였지? 그리고 이번 부산 출장 때 먹을 저녁 메뉴 하나만 추천해줘.")
    st2 = (await s2.get_session()).state
    print("세션2 state:", {k: v for k, v in st2.items() if not k.startswith("_")})


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("offline", "all"):
        asyncio.run(offline())
    if mode in ("llm", "all"):
        asyncio.run(with_llm())
