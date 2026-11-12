"""part02: Observe the lifecycle of a single request through Events (Gemini API key required).

Lecture Notes Part 2 Slides 21-28: User -> Runner -> Agent <-> Gemini <-> Tools, everything is recorded as Events.
Execution: uv run run_events.py
"""
import asyncio
import importlib

import _path  # noqa: F401
from common.bootstrap import require_llm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from chat_time_weather_agent.agent import root_agent


async def run_query(runner: Runner, session_id: str, prompt: str):
    print(f"\n================ [User Message] {prompt} ================")
    msg = types.Content(role="user", parts=[types.Part(text=prompt)])

    async for event in runner.run_async(user_id="u1", session_id=session_id, new_message=msg):
        print(f"--- Event author={event.author}")
        if event.get_function_calls():
            for fc in event.get_function_calls():
                print(f"  (1) Model tool call request: {fc.name}({fc.args})")
        if event.get_function_responses():
            for fr in event.get_function_responses():
                print(f"  (2) Runner tool execution result: {fr.response}")
        if event.actions and event.actions.state_delta:
            print("  state_delta:", dict(event.actions.state_delta))
        if event.is_final_response():
            print("  (3) Final response:\n", event.content.parts[0].text)


async def main():
    require_llm()
    ss = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name="demo", session_service=ss)
    session = await ss.create_session(app_name="demo", user_id="u1")

    # 1. Time and weather query (Observe tool call Events)
    await run_query(runner, session.id, "Tell me the current time and weather in Seoul")

    # 2. General query (Observe direct response Event without tool calls)
    await run_query(runner, session.id, "Hello! What can you help me with?")

    s = await ss.get_session(app_name="demo", user_id="u1", session_id=session.id)
    print(f"\nTotal events recorded in session: {len(s.events)}")


if __name__ == "__main__":
    asyncio.run(main())
