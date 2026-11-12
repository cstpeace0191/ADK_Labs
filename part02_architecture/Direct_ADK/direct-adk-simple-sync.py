# Sync Processing ADK Test
import asyncio
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai import types

load_dotenv(override=True)

agent = Agent(
    name="memory_assistant",
    model="gemini-2.5-flash",
    instruction="You are a helpful AI assistant who remembers user information and responds kindly."
)
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()
runner = Runner(agent=agent, app_name="my_adk_app", session_service=session_service, memory_service=memory_service)
user_id = "user_01"

# Create session (using asyncio.run when calling in synchronous environment)
session1 = asyncio.run(session_service.create_session(app_name="my_adk_app", user_id=user_id))

# Pass message as new_message argument
user_msg = types.Content(role="user", parts=[types.Part.from_text(text="Why is the sky blue?")])
events = runner.run(user_id=user_id, session_id=session1.id, new_message=user_msg)
for event in events:
    if event.is_final_response() and event.content and event.content.parts:
        text = "".join(p.text for p in event.content.parts if hasattr(p, "text") and p.text)
        print("Session 1 Response:", text)
