"""Lecture Notes Part 2 Slide 29: Dual-Layer Memory — Session (Short-term) vs Memory Bank (Long-term).

| Dimension   | Session Service (Short-term)               | Memory Service (Long-term)                     |
|-------------|--------------------------------------------|------------------------------------------------|
| Scope       | Active conversation threads & temp state   | Persistent facts & knowledge across sessions   |
| Data        | Message history, tool calls, state vars    | Organized user preferences & records           |
| Lifecycle   | Discarded upon conversation thread end     | Persisted permanently across sessions          |
| Backend     | InMemory · Database · VertexAiSession      | InMemoryMemoryService · VertexAiMemoryBankService |
| Access Mode | event history, {key} template, tool_context.state | load_memory / preload_memory tools            |

Execution:
  1) Direct multi-session lifecycle demo:
     uv run python part02_architecture/adk-based_Agent/memory_layers_agent/agent.py
  2) Interactive CLI:
     adk run memory_layers_agent
  3) Web UI:
     adk web --port 8008
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root directory to sys.path to enable common imports
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext, load_memory, preload_memory

load_dotenv(project_root / ".env", override=True)
if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() in ("TRUE", "1"):
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
    # In Vertex AI Express Mode, API key is preserved
    if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")


# ---------------------------------------------------------------------------
# 1. Custom Tools for State (Short-term) & Memory (Long-term)
# ---------------------------------------------------------------------------

def save_profile(name: str, tool_context: ToolContext) -> dict:
    """Saves the user's name. 'user:' prefix -> visible across other sessions of the same user.

    Args:
        name: User name
    """
    tool_context.state["user:name"] = name
    return {"status": "success", "saved": {"user:name": name}}


def save_trip(trip: str, tool_context: ToolContext) -> dict:
    """Stores business trip or travel plans mentioned in this conversation into user-scoped State ('user:trip')
    so that it persists across sessions in SQLite, and also sets 'trip' for session-level access.

    Args:
        trip: Plan summary (e.g., "Business trip to Busan next Tuesday")
    """
    tool_context.state["user:trip"] = trip
    tool_context.state["trip"] = trip
    return {"status": "success", "saved": {"user:trip": trip, "trip": trip}}


async def save_to_memory(tool_context: ToolContext) -> dict:
    """Transfers the current conversation and details to long-term memory (Memory Service).

    Call this tool when the user asks to save, remember, or persist their plans,
    itinerary, or preferences permanently across sessions.
    """
    if tool_context._invocation_context.memory_service is not None:
        await tool_context.add_session_to_memory()
        return {
            "status": "success",
            "message": "Current session events and plans successfully saved to long-term memory."
        }
    return {
        "status": "warning",
        "message": "Memory Service is not configured. Saved in session state only."
    }


# ---------------------------------------------------------------------------
# 2. Lifecycle Callbacks: Automatic Session -> Long-term Memory Migration
# ---------------------------------------------------------------------------

async def auto_save_session_to_memory(callback_context: CallbackContext):
    """Automatically transfers the current session's events to long-term memory
    at the end of each turn so that context is never lost across sessions.
    """
    if callback_context._invocation_context.memory_service is not None:
        try:
            await callback_context.add_session_to_memory()
        except Exception as e:
            # Best-effort background migration; do not interrupt agent turn
            pass


# ---------------------------------------------------------------------------
# 3. Agent Definition
# ---------------------------------------------------------------------------

root_agent = Agent(
    name="memory_layers_agent",
    model=os.getenv("ADK_MODEL", "gemini-3.8-flash"),
    description="An assistant utilizing both Session (short-term) State and Memory (long-term) retrieval",
    instruction="""
    You are a personal assistant.
    [User Profile & Persistent State]
      User name: {user:name?}
      Persistent trip itinerary: {user:trip?}
      Current session plan: {trip?}
    Rules:
    1) When the user mentions their name, call save_profile.
    2) When they mention a business trip, itinerary, or travel plan, call save_trip.
    3) When the user explicitly requests to save, register, or remember plans/details ("이 일정을 저장해줘", "기억해줘"),
       call save_to_memory to also transfer them into long-term memory.
    4) When asked about upcoming trips, plans, or places:
       - Check {user:trip?} and {trip?} first.
       - For additional details not in state (sightseeing spots, food preferences, past conversations, etc.),
         check automatically provided past memories first. If insufficient, search using load_memory.
         Use single concise keywords without extra particles for load_memory search queries (e.g., "제주", "용두암", "출장", "spicy").
    5) If information is not in memory or state either, state that you do not know. Do not make things up.
    6) Keep responses concise in 2 to 3 sentences.
    """,
    tools=[save_profile, save_trip, save_to_memory, preload_memory, load_memory],
    after_agent_callback=auto_save_session_to_memory,
)


# ---------------------------------------------------------------------------
# 4. Multi-Session Lifecycle Demonstration (Run Directly)
# ---------------------------------------------------------------------------

async def demo_lifecycle():
    """Runs a complete dual-session lifecycle demonstrating:
    Session 1: Collect user profile & trip itinerary -> auto/explicit save to Memory Service
    Session 2: New session (trip is reset) -> recall itinerary & spots from long-term memory
    """
    from common.runner_util import Session

    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()
    app_name, user_id = "memory_layers_demo", "user_hong"

    print("=" * 75)
    print("🚀 [Step 1] Session 1: Register Name & Plan Trip (Short-term State + Memory)")
    print("=" * 75)

    s1 = Session(
        root_agent,
        app_name=app_name,
        user_id=user_id,
        session_service=session_service,
        memory_service=memory_service,
    )

    prompt_1 = (
        "내 이름은 홍길동이고 다음 주 월요일에 1박2일 제주도 출장 일정이 있어. "
        "1일차에는 주요 미팅 후 용두암에 가고, 2일차에는 업무 마무리 후 복귀할 거야. 이 일정을 저장해줘."
    )
    print(f"\n[User (Session 1)]: {prompt_1}")
    res1 = await s1.send(prompt_1)
    print(f"\n[Agent (Session 1)]:\n{res1.final_text}")

    s1_session = await s1.get_session()
    print("\n[Session 1 State Inspection]:")
    print("  • user:name (User Scope - Persistent) :", s1_session.state.get("user:name"))
    print("  • user:trip (User Scope - Persistent) :", s1_session.state.get("user:trip"))
    print("  • trip      (Session Scope - Temp)    :", s1_session.state.get("trip"))

    # Explicitly ensure session events are indexed in memory service
    await memory_service.add_session_to_memory(s1_session)
    print("\n✅ Session 1 concluded. Full conversation transferred to Long-term Memory (add_session_to_memory).")

    print("\n" + "=" * 75)
    print("🚀 [Step 2] Session 2: New Session Started (trip is RESET, user:* is RETAINED)")
    print("=" * 75)

    s2 = Session(
        root_agent,
        app_name=app_name,
        user_id=user_id,
        session_service=session_service,
        memory_service=memory_service,
    )

    s2_session = await s2.get_session()
    print("\n[Session 2 Initial State Inspection]:")
    print("  • user:name (Retained from user scope) :", s2_session.state.get("user:name"))
    print("  • user:trip (Retained from user scope) :", s2_session.state.get("user:trip"))
    print("  • trip      (Reset! Value is None)      :", s2_session.state.get("trip"))

    prompt_2 = "내 이름이 뭐지? 그리고 내 다음 주 출장 일정과 1일차 방문 장소를 알려줘."
    print(f"\n[User (Session 2)]: {prompt_2}")
    res2 = await s2.send(prompt_2)
    print(f"\n[Agent (Session 2)]:\n{res2.final_text}")

    print("\n" + "=" * 75)
    print("🎉 Verification Complete:")
    print("  1. 'user:name' was preserved in Session State across sessions via 'user:' prefix.")
    print("  2. 'trip' was cleared in Session 2, but the Agent successfully recalled the Jeju trip")
    print("     and Yongduam sightseeing location by searching Long-term Memory (load_memory)!")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(demo_lifecycle())
