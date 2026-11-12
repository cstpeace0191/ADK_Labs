import os
import sys
import requests

# Ensure UTF-8 output (prevents encoding issues on Windows console)
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SERVER_URL = os.environ.get("SERVER_URL", "http://127.0.0.1:8000")
USER_ID = "user01"


def check_server_health(base_url: str) -> bool:
    """Checks if the FastAPI server is reachable."""
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def create_session(base_url: str, user_id: str) -> str:
    """Creates a new session on the server and returns the session_id."""
    try:
        resp = requests.post(f"{base_url}/sessions", json={"user_id": user_id}, timeout=5)
        if resp.status_code == 200:
            return resp.json().get("session_id")
    except requests.RequestException:
        pass
    return "default_session"


def send_chat_message(base_url: str, message: str, session_id: str, user_id: str) -> tuple[str, str]:
    """Sends a chat message to the FastAPI server and returns (response_text, session_id)."""
    payload = {
        "message": message,
        "session_id": session_id,
        "user_id": user_id,
    }
    resp = requests.post(f"{base_url}/chat", json=payload, timeout=60)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("response", "(No response)"), data.get("session_id", session_id)
    else:
        return f"[Server Error {resp.status_code}]: {resp.text}", session_id


def main():
    print("=" * 65)
    print("  💬 ADK Agent FastAPI Interactive Client")
    print(f"  Target Server: {SERVER_URL}")
    print("=" * 65)

    # 1. Verify server connectivity
    if not check_server_health(SERVER_URL):
        print(f"\n⚠️  Unable to connect to the server at {SERVER_URL}.")
        print("Please ensure the FastAPI server is running in another terminal:")
        print("  python direct-adk-fastapi-server.py")
        print("\nExiting.")
        sys.exit(1)

    # 2. Initialize session
    session_id = create_session(SERVER_URL, USER_ID)
    print(f"  Active Session : {session_id}")
    print("  Commands       : Type 'quit', 'exit', or 'q' to end.")
    print("  Capabilities   : Weather, time, and general QA (multi-turn chat)")
    print("=" * 65)

    # 3. Interactive conversational loop
    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEnding session. Goodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\nEnding session. Goodbye!")
            break

        print("🤖 Agent is thinking...", end="\r", flush=True)
        try:
            answer, session_id = send_chat_message(SERVER_URL, user_input, session_id, USER_ID)
            # Clear thinking status and print agent response
            print(" " * 30, end="\r")
            print(f"🤖 Agent: {answer}")
        except requests.RequestException as e:
            print(" " * 30, end="\r")
            print(f"⚠️  Request failed: {e}")


if __name__ == "__main__":
    main()

