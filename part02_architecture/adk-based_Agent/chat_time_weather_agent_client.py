"""Interactive CLI Client for chat_time_weather_agent via ADK api_server.

This client connects to an active `adk api_server` instance via REST (/run)
or Server-Sent Events (/run_sse) and provides an interactive conversational loop
with real-time display of tool calls (geocode, get_current_time, get_weather)
and multi-turn session persistence.

How to run:
  1) Terminal 1 (Start the ADK API server):
     cd part02_architecture/adk-based_Agent
     adk api_server --port 8000

     # Or from inside chat_time_weather_agent:
     # adk api_server . --port 8000

  2) Terminal 2 (Run this interactive client):
     python chat_time_weather_agent_client.py
     # Or from project root:
     # python part02_architecture/adk-based_Agent/chat_time_weather_agent/chat_time_weather_agent_client.py
"""
import argparse
import json
import os
import sys
import uuid
from typing import Any, Generator

import requests

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class AdkAgentClient:
    """HTTP client wrapper for Google ADK FastAPI server."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        app_name: str = "chat_time_weather_agent",
        user_id: str = "user_01",
        use_stream: bool = False,
        verbose: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.app_name = app_name
        self.user_id = user_id
        self.use_stream = use_stream
        self.verbose = verbose
        self.session_id: str | None = None

    def check_health(self) -> bool:
        """Verifies if the ADK api_server is reachable."""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=3)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def list_apps(self) -> list[str]:
        """Fetches the list of active agent apps served by the api_server."""
        try:
            resp = requests.get(f"{self.base_url}/list-apps", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except requests.RequestException:
            pass
        return []

    def create_session(self) -> str:
        """Creates a new session for the current user and app."""
        sid = f"session_{uuid.uuid4().hex[:8]}"
        url = f"{self.base_url}/apps/{self.app_name}/users/{self.user_id}/sessions/{sid}"
        try:
            resp = requests.post(url, json={"state": {}}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.session_id = data.get("id", sid)
                return self.session_id
        except requests.RequestException as e:
            if self.verbose:
                print(f"[Warning] Session creation via REST failed ({e}); falling back to local ID.")

        # Fallback to local session ID if endpoint not supported
        self.session_id = sid
        return self.session_id

    def run_turn(self, message: str) -> None:
        """Sends a user message to the agent and displays tool calls and responses."""
        if not self.session_id:
            self.create_session()

        payload = {
            "appName": self.app_name,
            "userId": self.user_id,
            "sessionId": self.session_id,
            "newMessage": {
                "role": "user",
                "parts": [{"text": message}],
            },
        }

        if self.use_stream:
            self._run_turn_sse(payload)
        else:
            self._run_turn_sync(payload)

    def _run_turn_sync(self, payload: dict) -> None:
        """Processes turn using the standard POST /run endpoint."""
        url = f"{self.base_url}/run"
        try:
            resp = requests.post(url, json=payload, timeout=60)
            if not resp.ok:
                print(f"\n❌ [Server Error {resp.status_code}]: {resp.text}")
                return

            events = resp.json()
            if not isinstance(events, list):
                print(f"\n❌ [Unexpected response format]: {events}")
                return

            self._render_events(events)
        except requests.RequestException as e:
            print(f"\n❌ [Network Error]: {e}")

    def _run_turn_sse(self, payload: dict) -> None:
        """Processes turn using the streaming POST /run_sse endpoint."""
        url = f"{self.base_url}/run_sse"
        try:
            with requests.post(url, json=payload, stream=True, timeout=90) as resp:
                if not resp.ok:
                    print(f"\n❌ [Server Error {resp.status_code}]: {resp.text}")
                    return

                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    if line.startswith("data:"):
                        raw_data = line[5:].strip()
                        if not raw_data:
                            continue
                        try:
                            event = json.loads(raw_data)
                            self._render_event(event)
                        except json.JSONDecodeError:
                            pass
        except requests.RequestException as e:
            print(f"\n❌ [Streaming Network Error]: {e}")

    def _render_events(self, events: list[dict]) -> None:
        """Renders an array of events returned by /run."""
        for ev in events:
            self._render_event(ev)

    def _render_event(self, ev: dict) -> None:
        """Renders a single event object."""
        content = ev.get("content") or {}
        parts = content.get("parts") or []
        author = ev.get("author") or self.app_name

        for p in parts:
            # 1. Function / Tool Call
            if "functionCall" in p:
                fc = p["functionCall"]
                fn_name = fc.get("name")
                fn_args = fc.get("args", {})
                args_str = json.dumps(fn_args, ensure_ascii=False)
                print(f"  ⚙️  [Tool Call] {fn_name}({args_str})")

            # 2. Tool Response
            elif "functionResponse" in p and self.verbose:
                fr = p["functionResponse"]
                fn_name = fr.get("name")
                fn_resp = fr.get("response")
                resp_preview = str(fn_resp)
                if len(resp_preview) > 120:
                    resp_preview = resp_preview[:117] + "..."
                print(f"  📥 [Tool Resp] {fn_name} -> {resp_preview}")

            # 3. Agent Final Response Text
            elif "text" in p and p.get("text"):
                text = p["text"].strip()
                if text:
                    print(f"\n🤖 [{author}]:\n{text}")


def run_interactive_client(client: AdkAgentClient) -> None:
    """Main interactive conversational loop in the terminal."""
    print("=" * 72)
    print("  🌍 chat_time_weather_agent — Interactive ADK API Client")
    print("=" * 72)
    print(f"  • Server URL : {client.base_url}")
    print(f"  • Agent App  : {client.app_name}")
    print(f"  • User ID    : {client.user_id}")
    print(f"  • Mode       : {'SSE Streaming (/run_sse)' if client.use_stream else 'REST Sync (/run)'}")
    print("=" * 72)

    # 1. Health check
    if not client.check_health():
        print(f"\n⚠️  Cannot connect to ADK api_server at {client.base_url}")
        print("Please ensure the api_server is running in another terminal:")
        print("  1) cd part02_architecture/adk-based_Agent")
        print("  2) adk api_server --port 8000")
        print("\nExiting.")
        sys.exit(1)

    # 2. Verify app registration
    apps = client.list_apps()
    if apps and client.app_name not in apps:
        print(f"\n⚠️  App '{client.app_name}' not found in active server apps: {apps}")
        if len(apps) == 1:
            client.app_name = apps[0]
            print(f"👉 Automatically switching to available app: '{client.app_name}'")
        else:
            print("Please restart api_server pointing to the directory containing chat_time_weather_agent.")

    # 3. Create initial session
    sid = client.create_session()
    print(f"  • Active Session : {sid}")
    print("\n[Commands]:")
    print("  /new or /reset : Start a new conversation session")
    print("  /stream        : Toggle SSE streaming mode on/off")
    print("  /apps          : View active apps on the server")
    print("  /help          : Show available commands")
    print("  exit or quit   : Exit the client")
    print("-" * 72)

    while True:
        try:
            user_input = input("\n🧑 [You] > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting client. Goodbye!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("exit", "quit", "q"):
            print("Exiting client. Goodbye!")
            break

        if cmd in ("/help", "help"):
            print("\nAvailable Commands:")
            print("  /new or /reset : Start a new session")
            print("  /stream        : Toggle between REST (/run) and SSE (/run_sse)")
            print("  /apps          : List registered apps on server")
            print("  exit or quit   : Exit")
            continue

        if cmd in ("/new", "/reset", "new", "reset"):
            new_sid = client.create_session()
            print(f"\n🔄 Session reset. New session started: {new_sid}")
            continue

        if cmd in ("/stream", "stream"):
            client.use_stream = not client.use_stream
            mode_name = "SSE Streaming (/run_sse)" if client.use_stream else "REST Sync (/run)"
            print(f"\n⚡ Streaming mode toggled: {mode_name}")
            continue

        if cmd in ("/apps", "apps"):
            active_apps = client.list_apps()
            print(f"\n📦 Active Apps on server ({client.base_url}): {active_apps}")
            continue

        # Send turn to agent
        client.run_turn(user_input)


def main():
    parser = argparse.ArgumentParser(
        description="Interactive CLI Client for chat_time_weather_agent via ADK api_server"
    )
    parser.add_argument(
        "--url",
        default=os.getenv("ADK_SERVER_URL", "http://127.0.0.1:8000"),
        help="ADK api_server base URL (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--app",
        default="chat_time_weather_agent",
        help="Target agent application name (default: chat_time_weather_agent)",
    )
    parser.add_argument(
        "--user",
        default="user_01",
        help="User identifier for session tracking (default: user_01)",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable Server-Sent Events (SSE) streaming by default",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Hide tool call details and show only final agent answers",
    )

    args = parser.parse_args()

    client = AdkAgentClient(
        base_url=args.url,
        app_name=args.app,
        user_id=args.user,
        use_stream=args.stream,
        verbose=not args.quiet,
    )

    run_interactive_client(client)


if __name__ == "__main__":
    main()

