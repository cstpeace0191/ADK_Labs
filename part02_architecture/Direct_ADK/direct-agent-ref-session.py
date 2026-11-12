import asyncio
import os
import sys
import warnings
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools.load_memory_tool import load_memory_tool
from google.genai import types

# Ensure UTF-8 output (prevents encoding issues on Windows console)
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 1. Load .env environment variables (override existing environment variables). API
load_dotenv(override=True)

# Prevent duplicate warning between GOOGLE_API_KEY and GEMINI_API_KEY (GEMINI_API_KEY takes precedence)
os.environ.pop("GOOGLE_API_KEY", None)

# Suppress warnings regarding ADK experimental features
warnings.filterwarnings("ignore", category=UserWarning)


# 2. Define Agent (add load_memory_tool)
agent = Agent(
    name="memory_assistant",
    model="gemini-2.5-flash",
    instruction="You are a helpful AI assistant who remembers user information and responds kindly.",
    tools=[load_memory_tool]
)

# 3. Create SessionService and MemoryService
# (Using In-Memory implementation for testing)
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

# 4. Bind services to Runner
runner = Runner(
    agent=agent,
    app_name="my_adk_app",
    session_service=session_service,
    memory_service=memory_service
)

async def main():
    user_id = "user_123"

    # -------------------------------------------------------------
    # Session 1: Register user information (Session 1)
    # -------------------------------------------------------------
    session1 = await session_service.create_session(app_name="my_adk_app", user_id=user_id)
    print(f"=== [Session 1 Started] ID: {session1.id[:8]} ===")
    
    prompt_1 = "Hi! My name is Alex, and my favorite fruit is apple."
    print(f"User: {prompt_1}")
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session1.id,
        new_message=types.Content(parts=[types.Part.from_text(text=prompt_1)])
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                text = "".join(part.text for part in event.content.parts if hasattr(part, "text") and part.text)
                if text:
                    print(f"Agent: {text}\n")

    # -------------------------------------------------------------
    # [Key] After Session 1 completes, persist session data to memory service (long-term memory)
    # -------------------------------------------------------------
    s1 = await session_service.get_session(
        app_name="my_adk_app", user_id=user_id, session_id=session1.id
    )
    await memory_service.add_session_to_memory(s1)
    print(">> [Memory Saved] Session 1 conversation has been saved to long-term memory (MemoryService).\n")

    # -------------------------------------------------------------
    # Session 2: Recall previous session long-term memory in a newly opened session (Session 2)
    # -------------------------------------------------------------
    session2 = await session_service.create_session(app_name="my_adk_app", user_id=user_id)
    print(f"=== [Session 2 Started (New Chat)] ID: {session2.id[:8]} ===")
    
    prompt_2 = "What fruit did I just say I like?"
    print(f"User: {prompt_2}")

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session2.id,
        new_message=types.Content(parts=[types.Part.from_text(text=prompt_2)])
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                text = "".join(part.text for part in event.content.parts if hasattr(part, "text") and part.text)
                if text:
                    print(f"Agent: {text}\n")

if __name__ == "__main__":
    asyncio.run(main())
