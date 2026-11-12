"""Lecture notes Part 2, slides 23-25, and Part 3, slide 39: direct Runner code—register, run, consume events (Gemini API key required).

Without the adk CLI, the application creates a Runner directly to run the agent loop.
The same my_agent/agent.py can also be run with `adk run my_agent` (adk handles step 1 below).

Run from the part03_cli folder: python run_direct_runner.py ["question"]
"""
import asyncio
import sys

import _path  # noqa: F401  (lab-root .env and retry settings)
from common.bootstrap import require_llm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from my_agent.agent import root_agent  # Agent definition from agent.py


async def main(question: str) -> None:
    require_llm()

    # 1. Register: create a Runner from root_agent and services.
    ss = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name="demo", session_service=ss)
    session = await ss.create_session(app_name="demo", user_id="u1")
    print(f"1. Register  Runner(agent={root_agent.name}, session_service=InMemorySessionService)")
    print(f"              Created session app_name=demo · user_id=u1 · session_id={session.id[:8]}…")

    # 2. Run: one run_async() call executes one agent loop cycle (steps 1-5 on slide 25).
    msg = types.Content(role="user", parts=[types.Part(text=question)])
    print(f"2. Run       run_async(new_message={question!r})")
    step = 0
    async for ev in runner.run_async(user_id="u1", session_id=session.id, new_message=msg):
        step += 1
        # 3. Consume: the application selects and uses events.
        for fc in ev.get_function_calls():
            print(f"   [Event {step}] Model call → function_call {fc.name}({dict(fc.args)})   (the model only requests)")
        for fr in ev.get_function_responses():
            print(f"   [Event {step}] Tool execution → function_response {fr.name}: {fr.response}   (executed by Runner)")
        if ev.actions and ev.actions.state_delta:
            print(f"   [Event {step}] state_delta {dict(ev.actions.state_delta)}")
        if ev.is_final_response() and ev.content and ev.content.parts:
            print(f"3. Consume  Final response (Event {step}): {ev.content.parts[0].text.strip()}")

    s = await ss.get_session(app_name="demo", user_id="u1", session_id=session.id)
    print(f"              {len(s.events)} events recorded in the session (user message · tool call · result · response)")
    print("\nThe application handles the rest (input loop · session store selection · HTTP server); "
          "the adk CLI handles these for you (see adk_internals.py).")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "What's the weather in Seoul?"))
