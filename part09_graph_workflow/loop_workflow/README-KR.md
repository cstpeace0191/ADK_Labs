# loop_workflow — 반복 및 재시도(Back-Edge) 그래프

특정 조건이 충족될 때까지 이전 노드로 역방향 엣지를 타고 반복 실행되는 순환 그래프 패턴입니다.

---

## 1. 그래프 구조

```
         ┌────────────────────────┐ (RETRY)
         ▼                        │
[START] ──▶ generate ──▶ evaluate ┴── (PASS) ──▶ [END]
```

- **엔트리포인트**: `agent.py`의 `root_agent`
- **종료 조건**:
  - `evaluate` 노드가 합격 점수에 도달하거나 최대 재시도 횟수를 초과하면 `route="PASS"`를 발행하여 무한 루프를 방지하고 종료합니다.

---

## 2. 실행 방법

🟢 **LLM 키 없이 실행 가능합니다.**

```bash
cd part09_graph_workflow
uv run run_workflows.py loop
```


