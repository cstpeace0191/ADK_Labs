"""part02: Observe ADK 2.0 Event fields (output, route, node path) — Runs without LLM.

Execution: python run_workflow_events.py
"""
import asyncio

import _path  # noqa: F401
from google.adk import Event, Workflow
from google.adk.runners import InMemoryRunner
from google.genai import types


def classify(node_input: str):
    return Event(output={"text": node_input},
                 route="LONG" if len(node_input) > 5 else "SHORT")


def long_msg(node_input: dict):
    return Event(message=f"Long input: {node_input['text']}")


def short_msg(node_input: dict):
    return Event(message=f"Short input: {node_input['text']}")


root_agent = Workflow(name="event_demo", edges=[
    ("START", classify),
    (classify, {"LONG": long_msg, "SHORT": short_msg}),
])


async def main():
    runner = InMemoryRunner(agent=root_agent, app_name="demo")
    s = await runner.session_service.create_session(app_name="demo", user_id="u1")
    for text in ["hello ADK", "hi"]:
        print(f"\n[user] {text}")
        msg = types.Content(role="user", parts=[types.Part(text=text)])
        async for ev in runner.run_async(user_id="u1", session_id=s.id, new_message=msg):
            node_info = getattr(ev, "node_info", None)
            path = getattr(node_info, "path", None)
            route = getattr(ev.actions, "route", None) if ev.actions else None
            text_out = ev.content.parts[0].text if ev.content and ev.content.parts else None
            print(f"  node={path!s:<28} route={route!s:<6} output={ev.output!s:<22} message={text_out}")


if __name__ == "__main__":
    asyncio.run(main())
