"""part03: adk api_server 의 REST(/run) · SSE(/run_sse) 엔드포인트 호출 클라이언트.

1) 터미널 A (part03_cli 폴더):  adk api_server --port 8000
2) 터미널 B:                    python api_client.py
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
        print("api_server가 실행 중이 아닙니다. part03_cli 폴더에서 `adk api_server --port 8000` 을 먼저 실행하세요.")
        return
    print("GET /list-apps ->", apps)
    if APP not in apps:
        print(f"⚠ '{APP}' 에이전트가 목록({apps})에 없습니다.")
        print("  api_server가 상위 폴더(ADK_Labs)에서 실행된 상태입니다.")
        print("  api_server를 종료(Ctrl+C)한 뒤 `part03_cli` 폴더에서 다시 실행하세요:")
        print("    cd part03_cli")
        print("    adk api_server --port 8000")
        return

    sid = f"s-{uuid.uuid4().hex[:6]}"
    r = requests.post(f"{BASE}/apps/{APP}/users/{USER}/sessions/{sid}", json={"state": {}})
    print("POST 세션 생성:", r.status_code, sid)

    body = {"app_name": APP, "user_id": USER, "session_id": sid,
            "new_message": {"role": "user", "parts": [{"text": "서울 날씨?"}]}}

    print("\n== POST /run (전체 이벤트 배열)")
    run_resp = requests.post(f"{BASE}/run", json=body, timeout=120)
    data = run_resp.json()
    if not run_resp.ok or not isinstance(data, list):
        print(f"⚠ /run 호출 실패 (HTTP {run_resp.status_code}): {data}")
        return
    for ev in data:
        print_parts(ev)

    print("\n== POST /run_sse (Server-Sent Events)")
    body["new_message"]["parts"][0]["text"] = "부산은?"
    with requests.post(f"{BASE}/run_sse", json=body, stream=True, timeout=120) as resp:
        for line in resp.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                print_parts(json.loads(line[5:]), prefix="SSE ")


if __name__ == "__main__":
    main()
