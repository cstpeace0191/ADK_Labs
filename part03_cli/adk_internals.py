"""Lecture notes Part 3, slides 31-38: reproduce ADK CLI setup using ADK internals.

Running `adk run my_agent` goes through these five steps
(`google.adk.cli.cli._setup_runner_context`, ADK 2.6.3):
  1. Discover the app or root_agent in the my_agent folder with AgentLoader.
  2. Load .env by searching upward from the agent folder (one .env at the lab root is enough).
  3. Create services from URI options; otherwise use local .adk storage
     (sessions: .adk/session.db, SQLite).
  4. Create Runner(app=…, session_service=…, artifact_service=…, memory_service=…).
  5. Provide an entry point: terminal input() loop for run, or run_async() per
     HTTP request for web/api_server.

Run from the part03_cli folder:
  python adk_internals.py                       🟢 Steps 1-4 only (no LLM call)
  python adk_internals.py --in_memory            🟢 Select services like adk run --in_memory
  python adk_internals.py --session_service_uri sqlite:///tmp_sessions.db
  python adk_internals.py --ask "Seoul weather?" 🔑 Run one turn, including step 5

Note: google.adk.cli.utils is an internal ADK API and may change between versions.
This is a learning reproduction. The default local-storage mode creates
my_agent/.adk/ as adk run does.
"""
import argparse
import asyncio
from pathlib import Path

import _path  # noqa: F401
from google.adk.cli.cli import _to_app
from google.adk.cli.utils import envs
from google.adk.cli.utils.agent_loader import AgentLoader
from google.adk.cli.utils.service_factory import (
    create_artifact_service_from_options,
    create_memory_service_from_options,
    create_session_service_from_options,
)
from google.adk.runners import Runner
from google.genai import types

AGENTS_DIR = Path(__file__).resolve().parent  # Parent folder from which adk run is launched
AGENT = "my_agent"


async def main(a: argparse.Namespace) -> None:
    # 1. Discover the agent.
    agent_or_app = AgentLoader(agents_dir=str(AGENTS_DIR)).load_agent(AGENT)
    print(f"1. Discover   AgentLoader → {type(agent_or_app).__name__} name={agent_or_app.name!r}"
          f" (from {AGENT}/agent.py)")

    # 2. Load .env.
    envs.load_dotenv_for_agent(AGENT, str(AGENTS_DIR))
    import os
    print(f"2. Load .env  GOOGLE_API_KEY set={bool(os.getenv('GOOGLE_API_KEY'))}"
          f" · ADK_MODEL={os.getenv('ADK_MODEL', '(default)')}")

    # 3. Create services using the same functions and defaults as adk run.
    session_uri = "memory://" if a.in_memory else a.session_service_uri
    use_local = not a.in_memory
    ss = create_session_service_from_options(base_dir=AGENTS_DIR, session_service_uri=session_uri,
                                             use_local_storage=use_local)
    arts = create_artifact_service_from_options(base_dir=AGENTS_DIR,
                                                artifact_service_uri="memory://" if a.in_memory else None,
                                                use_local_storage=use_local)
    mem = create_memory_service_from_options(base_dir=AGENTS_DIR, memory_service_uri=None)
    where = {"PerAgentDatabaseSessionService": f"→ {AGENT}/.adk/session.db (SQLite, created on first session)",
             "SqliteSessionService": f"→ {getattr(ss, '_db_path', '')}",
             "InMemorySessionService": "→ process memory (cleared on exit)"}.get(type(ss).__name__, "")
    print(f"3. Create services  session={type(ss).__name__} {where}")
    print(f"              artifact={type(arts).__name__} · memory={type(mem).__name__}")

    # 4. Create the Runner.
    app = _to_app(agent_or_app, AGENT)
    runner = Runner(app=app, session_service=ss, artifact_service=arts, memory_service=mem)
    print(f"4. Create Runner  Runner(app={app.name!r}, root_agent={app.root_agent.name!r})")

    # 5. Provide an entry point.
    if not a.ask:
        print("5. Entry point  adk run would start an input('[user]: ') loop → runner.run_async()"
              "\n                (pass --ask \"question\" to run one actual turn)")
        return
    session = await ss.create_session(app_name=AGENT, user_id="test_user")
    print(f"5. Entry point  [user]: {a.ask}")
    async for ev in runner.run_async(user_id="test_user", session_id=session.id,
                                     new_message=types.Content(role="user", parts=[types.Part(text=a.ask)])):
        for fc in ev.get_function_calls():
            print(f"              [{ev.author}] tool call: {fc.name} {dict(fc.args)}")
        if ev.is_final_response() and ev.content and ev.content.parts:
            print(f"              [{ev.author}]: {ev.content.parts[0].text.strip()}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Reproduce the steps ADK performs internally")
    p.add_argument("--in_memory", action="store_true", help="Use in-memory services like adk run --in_memory")
    p.add_argument("--session_service_uri", default=None, help="For example: sqlite:///tmp_sessions.db or memory://")
    p.add_argument("--ask", default=None, help="Run one turn for a question (Gemini API key required)")
    args = p.parse_args()
    if args.ask:
        from common.bootstrap import require_llm
        require_llm()
    asyncio.run(main(args))
