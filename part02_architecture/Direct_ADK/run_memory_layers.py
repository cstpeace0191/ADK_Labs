"""Lecture Notes Part 2 Slide 29: Dual-layer Memory — Directly inspect Session (short-term) vs Memory (long-term).

Execution:
  python run_memory_layers.py offline   LLM-free: Inspect storage scope, data, lifecycle, implementation, read methods via service API
  python run_memory_layers.py llm       Gemini key: Agent recalls memories via session State and load_memory/preload_memory
  python run_memory_layers.py all       Both (default)

offline directly calls what Runner does internally (recording events via append_event) to show storage structures.
Agent/workflow code does not append events to sessions directly (refer to Slide 28).
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
    """Session 1: Record a single conversation turn (message history + State change)."""
    s = await ss.create_session(app_name=APP, user_id=USER, session_id=session_id,
                                state={"app:notice": "Friday class canceled"})
    await ss.append_event(s, _user_turn("I am John. I cannot eat spicy food. I have a business trip to Busan next Tuesday."))
    await ss.append_event(s, _agent_turn("I will remember that, John.",
                                         {"user:name": "John", "trip": "Busan business trip next Tuesday",
                                          "temp:raw": "Value used only in this call"}))
    return await ss.get_session(app_name=APP, user_id=USER, session_id=s.id)


async def offline():
    print("=" * 70 + "\n[A] Session Service (Short-term)\n" + "=" * 70)
    ss = InMemorySessionService()
    s1 = await record_conversation(ss)
    print("(1) Data: Message history")
    for ev in s1.events:
        print(f"   - {ev.author:9}: {ev.content.parts[0].text}")
    print("(2) Data: State variables (Scope determined by prefix)")
    for k, v in s1.state.items():
        print(f"   - {k:10} = {v}")
    print("   -> temp:raw is not persisted:", "temp:raw" not in s1.state)

    s2 = await ss.create_session(app_name=APP, user_id=USER)
    print("(3) Storage scope: 'New' Session 2 for the same user")
    print(f"   - {len(s2.events)} events (conversation history exists only in Session 1)")
    print(f"   - user:name = {s2.state.get('user:name')}  (user: prefix has user scope)")
    print(f"   - trip      = {s2.state.get('trip')}  (no prefix = Session 1 only)")

    print("(4) Lifecycle & Implementation: Recreating service (= process restart)")
    restarted = InMemorySessionService()
    print("   - InMemorySessionService  ->",
          await restarted.get_session(app_name=APP, user_id=USER, session_id=s1.id), "(Lost)")
    DB.unlink(missing_ok=True)
    url = f"sqlite+aiosqlite:///{DB.as_posix()}"
    async with DatabaseSessionService(db_url=url) as db1:
        d1 = await record_conversation(db1, session_id="s-persist")
    async with DatabaseSessionService(db_url=url) as db2:  # Simulating restart: new instance
        again = await db2.get_session(app_name=APP, user_id=USER, session_id="s-persist")
        print(f"   - DatabaseSessionService  -> {len(again.events)} events, user:name={again.state.get('user:name')} (Preserved)")
    print("   - Production (GCP Managed): VertexAiSessionService (Agent Runtime)")

    print("\n" + "=" * 70 + "\n[B] Memory Service (Long-term)\n" + "=" * 70)
    memory = InMemoryMemoryService()
    await memory.add_session_to_memory(s1)  # Move to long-term memory once session ends
    print("(1) add_session_to_memory(Session 1) -> Stored as persistent knowledge across sessions")
    for q in ("Busan", "spicy", "Jeju", "to Busan"):
        res = await memory.search_memory(app_name=APP, user_id=USER, query=q)
        hits = [m.content.parts[0].text[:40] for m in res.memories]
        print(f"(2) search_memory('{q}') -> {len(hits)} results {hits}")
    print("   -> InMemory only checks exact word matching.")
    print("(3) Inaccessible to other users:",
          len((await memory.search_memory(app_name=APP, user_id="u2", query="Busan")).memories), "results")
    print("(4) Agents use this search via load_memory (on-demand) and preload_memory (auto per-turn) tools")
    print("   Production: VertexAiMemoryBankService — automatically extracts/merges facts with semantic search")
    DB.unlink(missing_ok=True)


async def with_llm():
    from common.bootstrap import require_llm
    from common.runner_util import Session
    from memory_layers_agent.agent import root_agent
    require_llm()
    ss, memory = InMemorySessionService(), InMemoryMemoryService()

    print("\n" + "=" * 70 + "\n[C] Verification with Agent (Gemini)\n" + "=" * 70)
    print("=== Session 1: Provide facts (stored in short-term State)")
    s1 = Session(root_agent, app_name=APP, user_id=USER, session_service=ss, memory_service=memory)
    await s1.send("Hello, I am John. I cannot eat spicy food, and I have a business trip to Busan next Tuesday.")
    st1 = (await s1.get_session()).state
    print("Session 1 state:", {k: v for k, v in st1.items() if not k.startswith("_")})
    await memory.add_session_to_memory(await s1.get_session())
    print("-> Save Session 1 to Memory (add_session_to_memory)")

    print("\n=== Session 2: New conversation — trip is gone, only user:name remains. Rest is retrieved from Memory")
    s2 = Session(root_agent, app_name=APP, user_id=USER, session_service=ss, memory_service=memory)
    # preload_memory searches with words in this sentence -> 'Busan' must be present for InMemory match
    await s2.send("What was my name? And please recommend a dinner menu for my business trip to Busan.")
    st2 = (await s2.get_session()).state
    print("Session 2 state:", {k: v for k, v in st2.items() if not k.startswith("_")})


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("offline", "all"):
        asyncio.run(offline())
    if mode in ("llm", "all"):
        asyncio.run(with_llm())
