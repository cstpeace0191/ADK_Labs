# route_workflow — 조건부 라우팅 분기 그래프

입력된 금액 조건에 따라 자동 승인 분기와 수동 검토 분기로 동적 라우팅하는 그래프 패턴입니다.

---

## 1. 그래프 구조

```
                  ┌── [AUTO] ──▶ auto_approve ──▶ [END]
[START] ──▶ route ┤
                  └── [REVIEW] ─▶ manual_review ─▶ [END]
```

- **엔트리포인트**: `agent.py`의 `root_agent`
- **라우팅 구현**:
  ```python
  def route(node_input: str):
      amount = int(node_input)
      if amount <= 100:
          return Event(route="AUTO", output=amount)
      return Event(route="REVIEW", output=amount)

  edges = [
      ("START", route),
      (route, {"AUTO": auto_approve, "REVIEW": manual_review}),
  ]
  ```

---

## 2. 실행 방법

🟢 **LLM API 키 없이 오프라인에서 즉시 실행 가능합니다.**

```bash
cd part09_graph_workflow
uv run run_workflows.py route
```


