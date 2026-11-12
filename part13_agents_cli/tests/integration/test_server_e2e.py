"""통합 테스트: 서버를 실제로 띄우고 두 입구(ADK HTTP API, A2A)를 HTTP 로 검사한다.

agents-cli 원본 tests/integration/test_server_e2e.py 를 a2a-sdk 0.3 / requests 만으로 줄였다.
  - test_agent_card     : 키 없이도 통과 (서버 기동 + Agent Card)
  - test_adk_run_sse    : Gemini 키 필요 (/run_sse SSE 스트림)
  - test_a2a_message    : Gemini 키 필요 (A2A JSON-RPC message/send)
실행: python -m pytest tests/integration -q
"""
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest
import requests

PORT = os.environ.get("TEST_SERVER_PORT", "8018")
BASE = f"http://127.0.0.1:{PORT}"
CARD_URL = f"{BASE}/a2a/app/.well-known/agent-card.json"
ROOT = Path(__file__).resolve().parents[2]


def _has_key() -> bool:
    sys.path.insert(0, str(ROOT.parent))
    from common.config import has_llm_credentials  # ADK_Labs 공통 헬퍼

    return has_llm_credentials()


needs_llm = pytest.mark.skipif(not _has_key(), reason="Gemini 키 없음")


@pytest.fixture(scope="session")
def server():
    env = {**os.environ, "APP_URL": BASE, "PYTHONWARNINGS": "ignore"}
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.fast_api_app:app", "--host", "127.0.0.1",
         "--port", PORT], cwd=ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):  # Agent Card 는 lifespan 이 끝나야 생긴다 → 준비 완료 신호
            try:
                if requests.get(CARD_URL, timeout=2).status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(1)
        else:
            pytest.fail("서버가 60초 안에 뜨지 않음")
        yield proc
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_agent_card(server):
    card = requests.get(CARD_URL, timeout=10).json()
    assert card["name"] == "agents_cli_workflow"
    assert card["url"].startswith(f"{BASE}/a2a/app")
    assert {s["name"] for s in card["skills"]} >= {"geocode", "get_weather", "get_current_time"}
    assert requests.get(f"{BASE}/list-apps", timeout=10).json() == ["app"]


@needs_llm
def test_adk_run_sse(server):
    user = f"user_{uuid.uuid4().hex[:8]}"
    sid = requests.post(f"{BASE}/apps/app/users/{user}/sessions", json={}, timeout=30).json()["id"]
    body = {"app_name": "app", "user_id": user, "session_id": sid, "streaming": True,
            "new_message": {"role": "user", "parts": [{"text": "안녕! 넌 무엇을 할 수 있어?"}]}}
    resp = requests.post(f"{BASE}/run_sse", json=body, stream=True, timeout=180)
    assert resp.status_code == 200
    events = [json.loads(line[6:]) for line in resp.iter_lines(decode_unicode=True)
              if line and line.startswith("data: ")]
    assert events, "SSE 이벤트가 없음"
    assert not any("error" in e for e in events), events[-1]
    texts = [p.get("text", "") for e in events for p in (e.get("content") or {}).get("parts", [])]
    assert any(t.strip() for t in texts)


@needs_llm
def test_a2a_message(server):
    rpc = {"jsonrpc": "2.0", "id": "1", "method": "message/send",
           "params": {"message": {"role": "user", "messageId": uuid.uuid4().hex,
                                  "parts": [{"kind": "text", "text": "프랑스의 수도는?"}]}}}
    result = requests.post(f"{BASE}/a2a/app", json=rpc, timeout=180).json()["result"]
    assert result["status"]["state"] == "completed"
    text = json.dumps(result, ensure_ascii=False)
    assert "파리" in text or "Paris" in text
