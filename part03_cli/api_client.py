"""part03: Client for calling the REST (/run) and SSE (/run_sse) endpoints of adk api_server.

1) Terminal A (part03_cli folder): adk api_server --port 8000
2) Terminal B:                    python api_client.py
"""
import json
import sys
import uuid

import requests

BASE = "http://localhost:8000"
APP, USER = "my_agent", "u1"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def print_parts(ev: dict, prefix: str = "") -> None:
    for p in (ev.get("content") or {}).get("parts", []):
        if "functionCall" in p:
            fc = p["functionCall"]
            print(f"{prefix}[{ev.get('author')}] tool call: {fc['name']} {fc.get('args')}")
        elif "functionResponse" in p:
            print(f"{prefix}[{ev.get('author')}] tool resp: {p['functionResponse'].get('response')}")
        elif p.get("text"):
            print(f"{prefix}[{ev.get('author')}] {p['text']}")


def main():
    try:
        apps = requests.get(f"{BASE}/list-apps", timeout=5).json()
    except requests.ConnectionError:
        print("api_server is not running. Start it first from part03_cli with `adk api_server --port 8000`.")
        return
    print("GET /list-apps ->", apps)
    if APP not in apps:
        print(f"⚠ Agent '{APP}' is not in the list ({apps}).")
        print("  api_server may have been started from the parent ADK_Labs folder.")
        print("  Stop api_server (Ctrl+C), then restart it from the `part03_cli` folder:")
        print("    cd part03_cli")
        print("    adk api_server --port 8000")
        return

    sid = f"s-{uuid.uuid4().hex[:6]}"
    r = requests.post(f"{BASE}/apps/{APP}/users/{USER}/sessions/{sid}", json={"state": {}})
    print("POST create session:", r.status_code, sid)

    body = {"app_name": APP, "user_id": USER, "session_id": sid,
            "new_message": {"role": "user", "parts": [{"text": "Seoul weather?"}]}}

    print("\n== POST /run (complete event array)")
    run_resp = requests.post(f"{BASE}/run", json=body, timeout=120)
    data = run_resp.json()
    if not run_resp.ok or not isinstance(data, list):
        print(f"⚠ /run request failed (HTTP {run_resp.status_code}): {data}")
        return
    for ev in data:
        print_parts(ev)

    print("\n== POST /run_sse (Server-Sent Events)")
    body["new_message"]["parts"][0]["text"] = "What about Busan?"
    with requests.post(f"{BASE}/run_sse", json=body, stream=True, timeout=120) as resp:
        for line in resp.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                print_parts(json.loads(line[5:]), prefix="SSE ")


if __name__ == "__main__":
    main()
