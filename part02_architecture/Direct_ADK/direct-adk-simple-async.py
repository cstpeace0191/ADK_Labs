import asyncio
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai import types
load_dotenv(override=True)

# 1. Define agent and memory/session services
agent = Agent(
    name="memory_assistant",
    model="gemini-3.5-flash",
    instruction="You are a helpful AI assistant who remembers user information and responds kindly."
)

# 2. Define session and memory services
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

# 3. Define Runner
runner = Runner(
    agent=agent,
    app_name="my_adk_app",
    session_service=session_service,
    memory_service=memory_service
)

# 4. Define async main function
async def main():
    user_id = "user_01"
    
    # [Step 1] Create session & inject info
    session1 = await session_service.create_session(app_name="my_adk_app", user_id=user_id)
    
    # [Step 2] Create message (using types.Content)
    prompt_text = "Why is the sky blue?"
    user_message = types.Content(role="user", parts=[types.Part.from_text(text=prompt_text)])
    
    # [Step 3] Execute Runner asynchronously and receive events
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session1.id,
        new_message=user_message
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = "".join(p.text for p in event.content.parts if hasattr(p, "text") and p.text)
                print("Session 1 Response:", response_text)
if __name__ == "__main__":
    asyncio.run(main())
