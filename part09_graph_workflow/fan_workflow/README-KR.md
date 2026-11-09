# fan_workflow — 병렬 실행(Fan-Out) 및 취합(Fan-In) 그래프

동일한 입력을 여러 워커 노드에 동시에 전달하여 병렬로 처리한 뒤, 결과를 하나의 사전으로 통합(`JoinNode`)하는 패턴입니다.

---

## 1. 그래프 구조

```
                  ┌──▶ worker_weather ──┐
[START] ──▶ split ┼──▶ worker_traffic ──┼──▶ JoinNode ──▶ [END]
                  └──▶ worker_news    ──┘
```

- **엔트리포인트**: `agent.py`의 `root_agent`
- **핵심 메커니즘**:
  - `JoinNode`가 모든 선행 병렬 브랜치의 작업 완료를 기다린 후 결과를 모아 다음 노드에 취합 딕셔너리로 전달합니다.

---

## 2. 실행 방법

🟢 **LLM 키 없이 실행 가능합니다.**

```bash
cd part09_graph_workflow
uv run run_workflows.py fan
```


