"""Interactive Cloud Run ADK Agent Client.

Connects to an ADK Agent service deployed on Google Cloud Run
(e.g., https://adk-default-service-name-1008280623664.asia-northeast3.run.app)
and provides an interactive terminal session with multi-turn conversation,
real-time tool execution tracking, and session management.

Usage:
  # 1. Direct interactive mode (prompts for URL if not provided)
  python cloud_run_agent.py

  # 2. Specify Cloud Run URL via command line
  python cloud_run_agent.py --url https://adk-default-service-name-1008280623664.asia-northeast3.run.app

  # 3. Specify options (streaming, user, target app)
  python cloud_run_agent.py --url <YOUR_URL> --stream --user user_hong
"""
import argparse
import json
import os
import re
import sys
import uuid
from typing import Optional
from urllib.parse import urlparse

import requests

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEFAULT_CLOUD_RUN_URL = "https://adk-default-service-name-1008280623664.asia-northeast3.run.app"
DEFAULT_USER_ID = "cloud_user_01"


def get_google_id_token(target_url: str) -> Optional[str]:
    """Attempts to obtain a Google Cloud ID token if authentication is needed."""
    # 1. Try google-auth library
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token
        req = google.auth.transport.requests.Request()
        return google.oauth2.id_token.fetch_id_token(req, target_url)
    except Exception:
        pass

    # 2. Try gcloud CLI
    try:
        import subprocess
        res = subprocess.run(
            ["gcloud", "auth", "print-identity-token"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        token = res.stdout.strip()
        if token:
            return token
    except Exception:
        pass

    return None


class CloudRunAgentClient:
    """Client for Google Cloud Run ADK Agent microservices."""

    def __init__(
        self,
        base_url: str,
        app_name: Optional[str] = None,
        user_id: str = DEFAULT_USER_ID,
        use_stream: bool = False,
        verbose: bool = True,
        use_auth: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.app_name = app_name
        self.user_id = user_id
        self.use_stream = use_stream
        self.verbose = verbose
        self.use_auth = use_auth
        self.session_id: Optional[str] = None
        self._session = requests.Session()

    def _get_headers(self) -> dict:
        """Constructs headers, including Google Cloud ID token if enabled."""
        headers = {
            "Content-Type": "application/json",
            "Connection": "close",  # Avoid stale SSL keep-alive sockets on Cloud Run
            "User-Agent": "ADK-CloudRun-Client/1.0",
        }
        if self.use_auth:
            token = get_google_id_token(self.base_url)
            if token:
                headers["Authorization"] = f"Bearer {token}"
        return headers

    def check_health(self) -> bool:
        """Checks whether the Cloud Run service is online and healthy."""
        try:
            resp = self._session.get(
                f"{self.base_url}/health",
                headers=self._get_headers(),
                timeout=10,
            )
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def list_apps(self) -> list[str]:
        """Queries /list-apps to discover registered ADK applications."""
        try:
            resp = self._session.get(
                f"{self.base_url}/list-apps",
                headers=self._get_headers(),
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
        except requests.RequestException:
            pass
        return []

    def create_session(self) -> str:
        """Initializes a new session on the Cloud Run server."""
        sid = f"sess_{uuid.uuid4().hex[:8]}"
        target_app = self.app_name or "chat_time_weather_agent"
        url = f"{self.base_url}/apps/{target_app}/users/{self.user_id}/sessions/{sid}"

        try:
            resp = self._session.post(
                url,
                json={"state": {}},
                headers=self._get_headers(),
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.session_id = data.get("id", sid)
                return self.session_id
        except requests.RequestException as e:
            if self.verbose:
                print(f"[Notice] Remote session init note: {e}; using ID {sid}")

        self.session_id = sid
        return self.session_id

    def run_turn(self, message: str) -> None:
        """Executes one conversational turn against the Cloud Run agent."""
        if not self.session_id:
            self.create_session()

        payload = {
            "appName": self.app_name or "chat_time_weather_agent",
            "userId": self.user_id,
            "sessionId": self.session_id,
            "newMessage": {
                "role": "user",
                "parts": [{"text": message}],
            },
        }

        if self.use_stream:
            self._run_sse(payload)
        else:
            self._run_sync(payload)

    def _run_sync(self, payload: dict) -> None:
        """Sends query via POST /run (synchronous complete event array)."""
        url = f"{self.base_url}/run"
        try:
            resp = self._session.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=60,
            )
            if not resp.ok:
                print(f"\n❌ [Cloud Run Error {resp.status_code}]: {resp.text}")
                return

            events = resp.json()
            if not isinstance(events, list):
                print(f"\n❌ [Unexpected response payload]: {events}")
                return

            for ev in events:
                self._render_event(ev)

        except requests.RequestException as e:
            print(f"\n❌ [Network Connection Error]: {e}")

    def _run_sse(self, payload: dict) -> None:
        """Streams query response via POST /run_sse."""
        url = f"{self.base_url}/run_sse"
        try:
            with self._session.post(
                url,
                json=payload,
                headers=self._get_headers(),
                stream=True,
                timeout=90,
            ) as resp:
                if not resp.ok:
                    print(f"\n❌ [Cloud Run Error {resp.status_code}]: {resp.text}")
                    return

                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    if line.startswith("data:"):
                        raw = line[5:].strip()
                        if not raw:
                            continue
                        try:
                            ev = json.loads(raw)
                            self._render_event(ev)
                        except json.JSONDecodeError:
                            pass

        except requests.RequestException as e:
            print(f"\n❌ [Streaming Connection Error]: {e}")

    def _render_event(self, ev: dict) -> None:
        """Parses and renders an ADK event (tool call, response, text)."""
        content = ev.get("content") or {}
        parts = content.get("parts") or []
        author = ev.get("author") or self.app_name or "Agent"

        for p in parts:
            if "functionCall" in p:
                fc = p["functionCall"]
                fn_name = fc.get("name")
                fn_args = fc.get("args", {})
                args_str = json.dumps(fn_args, ensure_ascii=False)
                print(f"  ⚙️  [Cloud Tool Call] {fn_name}({args_str})")

            elif "functionResponse" in p and self.verbose:
                fr = p["functionResponse"]
                fn_name = fr.get("name")
                fn_resp = fr.get("response")
                preview = str(fn_resp)
                if len(preview) > 120:
                    preview = preview[:117] + "..."
                print(f"  📥 [Cloud Tool Resp] {fn_name} -> {preview}")

            elif "text" in p and p.get("text"):
                text = p["text"].strip()
                if text:
                    print(f"\n🤖 [{author}]:\n{text}")


def extract_region(url: str) -> str:
    """Extracts Cloud Run region from domain name if available."""
    match = re.search(r"\.([a-z0-9-]+)\.run\.app", url)
    return match.group(1) if match else "global"


def run_interactive_loop(client: CloudRunAgentClient) -> None:
    """Interactive command-line chat session with the Cloud Run service."""
    region = extract_region(client.base_url)

    print("=" * 76)
    print("  ☁️  Google Cloud Run ADK Agent — Interactive Client")
    print("=" * 76)
    print(f"  • Service URL : {client.base_url}")
    print(f"  • GCP Region  : {region}")
    print(f"  • Active App  : {client.app_name}")
    print(f"  • User ID     : {client.user_id}")
    print(f"  • Mode        : {'SSE Streaming (/run_sse)' if client.use_stream else 'REST Sync (/run)'}")
    print("=" * 76)

    # 1. Verify health
    print("🔍 Connecting to Cloud Run service...", end=" ", flush=True)
    if client.check_health():
        print("✅ Online (HTTP 200 OK)")
    else:
        print("⚠️ Warning: Health check endpoint did not return 200 OK.")
        print("   The service might be cold-starting or require IAM authorization.")

    # 2. Check and select active app
    apps = client.list_apps()
    if apps:
        if not client.app_name:
            client.app_name = apps[0]
        elif client.app_name not in apps:
            print(f"👉 Target app '{client.app_name}' not in {apps}; switching to '{apps[0]}'")
            client.app_name = apps[0]
        print(f"📦 Deployed Apps : {apps} (Selected: {client.app_name})")
    else:
        if not client.app_name:
            client.app_name = "chat_time_weather_agent"
        print(f"📦 Active App    : {client.app_name} (Default)")

    # 3. Create initial session
    sid = client.create_session()
    print(f"🔑 Active Session: {sid}")
    print("\n[Available Commands]:")
    print("  /new or /reset : Start a new conversation session")
    print("  /url <new_url> : Switch to a different Cloud Run service URL")
    print("  /stream        : Toggle SSE streaming mode on/off")
    print("  /apps          : Query available agent apps on the service")
    print("  /help          : Show this command menu")
    print("  exit or quit   : Exit the interactive client")
    print("-" * 76)

    while True:
        try:
            user_input = input("\n🧑 [You] > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting Cloud Run client. Goodbye!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("exit", "quit", "q"):
            print("Exiting Cloud Run client. Goodbye!")
            break

        if cmd in ("/help", "help"):
            print("\nAvailable Commands:")
            print("  /new or /reset : Start a new session")
            print("  /url <new_url> : Connect to another Cloud Run endpoint")
            print("  /stream        : Toggle between REST (/run) and SSE (/run_sse)")
            print("  /apps          : View apps deployed on current Cloud Run service")
            print("  exit or quit   : Exit")
            continue

        if cmd.startswith("/url"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                new_url = parts[1].strip().rstrip("/")
                client.base_url = new_url
                print(f"\n🔄 Switched target service URL to: {client.base_url}")
                apps = client.list_apps()
                if apps:
                    client.app_name = apps[0]
                    print(f"  • Detected apps: {apps}")
                sid = client.create_session()
                print(f"  • New session initialized: {sid}")
            else:
                print(f"Current URL: {client.base_url}\nUsage: /url https://<service-name>.run.app")
            continue

        if cmd in ("/new", "/reset", "new", "reset"):
            new_sid = client.create_session()
            print(f"\n🔄 Session reset. New session started: {new_sid}")
            continue

        if cmd in ("/stream", "stream"):
            client.use_stream = not client.use_stream
            mode_name = "SSE Streaming (/run_sse)" if client.use_stream else "REST Sync (/run)"
            print(f"\n⚡ Mode toggled: {mode_name}")
            continue

        if cmd in ("/apps", "apps"):
            active_apps = client.list_apps()
            print(f"\n📦 Apps deployed on {client.base_url}: {active_apps}")
            continue

        # Send turn to Cloud Run agent
        client.run_turn(user_input)


def main():
    parser = argparse.ArgumentParser(
        description="Interactive Client for Google Cloud Run ADK Agent Services"
    )
    parser.add_argument(
        "--url",
        "-u",
        default=os.getenv("CLOUD_RUN_URL"),
        help=f"Cloud Run service URL (default: {DEFAULT_CLOUD_RUN_URL})",
    )
    parser.add_argument(
        "--app",
        "-a",
        default=None,
        help="Target agent application name (default: auto-detected or chat_time_weather_agent)",
    )
    parser.add_argument(
        "--user",
        default=DEFAULT_USER_ID,
        help=f"User identifier for session tracking (default: {DEFAULT_USER_ID})",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable Server-Sent Events (SSE) streaming by default",
    )
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Attach Google Cloud ID token in Authorization header for private Cloud Run services",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Hide tool call details and show only final agent answers",
    )

    args = parser.parse_args()

    # Determine Cloud Run URL
    target_url = args.url
    if not target_url:
        print("=" * 76)
        print("  ☁️  Google Cloud Run Service Connection")
        print("=" * 76)
        prompt_text = f"Enter Cloud Run service URL\n[Press Enter for default: {DEFAULT_CLOUD_RUN_URL}]:\n> "
        try:
            user_entered_url = input(prompt_text).strip()
            target_url = user_entered_url if user_entered_url else DEFAULT_CLOUD_RUN_URL
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            sys.exit(0)

    # Normalize URL
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = "https://" + target_url
    target_url = target_url.rstrip("/")

    client = CloudRunAgentClient(
        base_url=target_url,
        app_name=args.app,
        user_id=args.user,
        use_stream=args.stream,
        verbose=not args.quiet,
        use_auth=args.auth,
    )

    run_interactive_loop(client)


if __name__ == "__main__":
    main()

