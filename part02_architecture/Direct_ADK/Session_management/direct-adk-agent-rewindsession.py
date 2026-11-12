import asyncio
import os
import sys
import warnings
from dotenv import load_dotenv

# Ensure UTF-8 output (prevents encoding issues on Windows console)
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load .env environment variables (override existing environment variables)
load_dotenv(override=True)

# Synchronize API key environment variables
if os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
elif os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

# Suppress unnecessary warnings regarding ADK experimental features
warnings.filterwarnings("ignore", category=UserWarning)

from google.adk.agents import Agent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext
from google.genai import types

# ---------------------------------------------------------------------------
# 1. Define Tools for Working Memory (State) manipulation
# ---------------------------------------------------------------------------
def set_state_color(color: str, tool_context: ToolContext) -> str:
    """Sets or updates the color in the session state (working memory).

    Args:
        color (str): The color name (e.g., 'red', 'blue', 'green').

    Returns:
        str: Confirmation message.
    """
    tool_context.state["color"] = color
    return f"State color has been set to '{color}'."


def get_state_color(tool_context: ToolContext) -> str:
    """Retrieves the current color from the session state.

    Returns:
        str: The current color in state.
    """
    color = tool_context.state.get("color", "No color is set.")
    return f"Current state color is '{color}'."


# ---------------------------------------------------------------------------
# 2. Configure Agent
# ---------------------------------------------------------------------------
agent = Agent(
    name="color_agent",
    model="gemini-3.5-flash",
    instruction=(
        "You are an assistant managing session state (Working Memory).\n"
        "When the user asks to set or change a color, always call the `set_state_color` tool.\n"
        "When asked about the current state color, use the `get_state_color` tool."
    ),
    tools=[set_state_color, get_state_color],
)

# ---------------------------------------------------------------------------
# 3. Configure Runner
#    When using Runner directly, explicitly inject session_service,
#    artifact_service, and memory_service.
# ---------------------------------------------------------------------------
APP_NAME = "color_app"
USER_ID = "user01"

runner = Runner(
    agent=agent,
    app_name=APP_NAME,
    session_service=InMemorySessionService(),
    artifact_service=InMemoryArtifactService(),
    memory_service=InMemoryMemoryService(),
)


# ---------------------------------------------------------------------------
# 4. Async agent call wrapper function (call_agent_async)
# ---------------------------------------------------------------------------
async def call_agent_async(
    runner: Runner, user_id: str, session_id: str, prompt: str
) -> list:
    """Wrapper function to send a message to the agent and return the list of generated events."""
    print(f"\n[User] {prompt}")
    events_list = []
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(parts=[types.Part.from_text(text=prompt)]),
    ):
        events_list.append(event)
        if event.is_final_response():
            if event.content and event.content.parts:
                text = "".join(
                    part.text
                    for part in event.content.parts
                    if hasattr(part, "text") and part.text
                ).strip()
                if text:
                    print(f"[Agent] {text}")
    return events_list


# ---------------------------------------------------------------------------
# 5. Session management and Rewind async execution routine
# ---------------------------------------------------------------------------
async def main():
    # 5-1. Create session (using runner.session_service)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )
    print(f"=== [Session Created] ID: {session.id} ===")
    print(f"Initial Session State: {session.state}")

    # 5-2. First call: set color to 'red'
    print("\n--- [Step 1] Set state color to red ---")
    await call_agent_async(
        runner, USER_ID, session.id, "set state color to red"
    )
    s1 = await runner.session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session.id
    )
    print(f">> State check: {s1.state}")

    # 5-3. Second call: update color to 'blue' (this change will be rolled back later)
    print("\n--- [Step 2] Update state color to blue ---")
    events_list = await call_agent_async(
        runner, USER_ID, session.id, "update state color to blue"
    )
    s2 = await runner.session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session.id
    )
    print(f">> State check: {s2.state}")

    # 5-4. Extract invocation_id to roll back
    # Retrieve invocation_id of the second call from events_list
    rewind_invocation_id = (
        events_list[1].invocation_id
        if len(events_list) > 1
        else events_list[0].invocation_id
    )
    print(f"\n[Target Invocation ID]: {rewind_invocation_id}")

    # 5-5. Execute Rewind (roll back to before blue update -> restore red state)
    print("--- [Step 3] Execute rewind_async (revert blue update) ---")
    await runner.rewind_async(
        user_id=USER_ID,
        session_id=session.id,
        rewind_before_invocation_id=rewind_invocation_id,
    )
    print(">> Session Rewind complete!")

    # 5-6. Check session State and conversation after Rewind
    s3 = await runner.session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session.id
    )
    print(f">> Restored State after Rewind (color should be red): {s3.state}")

    # 5-7. Query the agent in the restored session for current color
    print("\n--- [Step 4] Query agent for current color after Rewind ---")
    await call_agent_async(
        runner, USER_ID, session.id, "what is the current state color?"
    )


if __name__ == "__main__":
    asyncio.run(main())
