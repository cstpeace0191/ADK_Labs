"""agents-cli run --mode adk|a2a 가 내부에서 보내는 HTTP 요청을 그대로 재현한다.

  python client.py adk "서울 날씨 알려줘"       # ADK HTTP API: 세션 생성 → POST /run_sse (SSE)
  python client.py a2a "도쿄는 지금 몇 시야?"   # A2A: Agent Card 조회 → POST /a2a/app (JSON-RPC message/send)
  python client.py card                          # Agent Card 만 출력

같은 내용을 agents-cli 로 하면:
  agents-cli run --url http://127.0.0.1:8008 --mode adk --app-name app "서울 날씨 알려줘"
  agents-cli run --url http://127.0.0.1:8008 --mode a2a --app-name app "도쿄는 지금 몇 시야?"

먼저 서버를 띄운다:  python -m uvicorn app.fast_api_app:app --port 8008
배포한 에이전트에 붙으려면 BASE_URL 환경변수를 바꾼다 (Cloud Run 은 인증 헤더 필요 → README).
"""
import json
import os
import sys
import uuid

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.getenv("BASE_URL", "http://127.0.0.1:8008").rstrip("/")
APP = os.getenv("APP_NAME", "app")


def run_adk(text: str) -> None:
    user = "cli-user"
    # 1) 세션 생성: POST /apps/{app}/users/{user}/sessions  (초기 state 를 넣을 수 있다)
    sid = requests.post(f"{BASE}/apps/{APP}/users/{user}/sessions",
                        json={"state": {"preferred_language": "Korean"}}, timeout=30).json()["id"]
    print(f"[session] {sid}")
    # 2) 실행: POST /run_sse  → "data: {Event JSON}" 줄이 스트리밍된다
    body = {"app_name": APP, "user_id": user, "session_id": sid, "streaming": True,
            "new_message": {"role": "user", "parts": [{"text": text}]}}
    with requests.post(f"{BASE}/run_sse", json=body, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            ev = json.loads(line[6:])
            if "error" in ev:
                print("[error]", ev["error"])
            if ev.get("partial"):  # 스트리밍 조각: 같은 내용이 최종 이벤트로 한 번 더 온다
                continue
            for p in (ev.get("content") or {}).get("parts", []):
                if fc := p.get("functionCall"):
                    print(f"[tool_call] {fc['name']}({json.dumps(fc.get('args', {}), ensure_ascii=False)})")
                elif fr := p.get("functionResponse"):
                    print(f"[tool_response] {fr['name']} -> {str(fr.get('response'))[:80]}...")
                elif p.get("text"):
                    print(f"[{ev.get('author')}] {p['text']}")


def get_card() -> dict:
    return requests.get(f"{BASE}/a2a/{APP}/.well-known/agent-card.json", timeout=30).json()


def run_a2a(text: str) -> None:
    card = get_card()  # 1) 명함에서 호출할 URL 을 얻는다
    card_url = card.get("url")
    if not card_url:
        interfaces = card.get("supportedInterfaces") or []
        if interfaces and isinstance(interfaces, list):
            card_url = interfaces[0].get("url")
    if not card_url:
        card_url = f"{BASE}/a2a/{APP}"
    if BASE not in card_url and "/a2a/" in card_url:
        path = card_url.split("/a2a/", 1)[1]
        card_url = f"{BASE}/a2a/{path}"

    print(f"[card] {card['name']} → {card_url}")
    rpc = {"jsonrpc": "2.0", "id": uuid.uuid4().hex, "method": "message/send",
           "params": {"message": {"role": "user", "messageId": uuid.uuid4().hex,
                                  "parts": [{"kind": "text", "text": text}]}}}
    # 2) JSON-RPC message/send → Task(상태 + artifacts) 가 돌아온다
    result = requests.post(card_url, json=rpc, timeout=300).json()["result"]
    print(f"[task] id={result['id']} state={result['status']['state']}")
    for art in result.get("artifacts", []):
        for p in art.get("parts", []):
            if p.get("kind") == "text":
                print(f"[agent] {p['text']}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "adk"
    msg = sys.argv[2] if len(sys.argv) > 2 else "서울의 현재 날씨와 현지 시각을 알려줘"
    if mode == "card":
        print(json.dumps(get_card(), ensure_ascii=False, indent=2))
    elif mode == "a2a":
        run_a2a(msg)
    else:
        run_adk(msg)
