# a2a_demo — Agent-to-Agent (A2A) 원격 통신 데모

두 개의 독립된 에이전트(`host_agent`와 `prime_agent`)가 표준 A2A 프로토콜(Agent Card + JSON-RPC)을 통해 원격으로 협업하는 실습입니다.

---

## 1. 아키텍처 및 역할

```
[사용자] ──▶ host_agent (클라이언트)
                 │
                 ▼ (A2A JSON-RPC 호출: http://localhost:8001/a2a)
             prime_agent (소수 판별 전담 서버)
```

1. **`prime_agent` (A2A 서버)**:
   - FastAPI 기반 A2A 엔드포인트(`a2a_app`) 노출
   - 소수 판별 도구(`is_prime`)를 탑재하고 Agent Card를 발행
2. **`host_agent` (A2A 클라이언트)**:
   - `RemoteA2aAgent` 클래스를 사용하여 원격 `http://localhost:8001`을 도구처럼 에이전트에 부착

---

## 2. 실행 방법

`part11_eval_deploy` 폴더에서 진행합니다:

```bash
cd part11_eval_deploy

# 터미널 1: prime_agent 서버 기동 (8001번 포트)
uv run uvicorn a2a_demo.prime_agent.agent:a2a_app --port 8001

# 터미널 2: host_agent 질의 실행
uv run run_a2a_client.py
```


