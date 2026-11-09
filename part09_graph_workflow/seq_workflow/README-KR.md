# seq_workflow — 순차 실행 그래프 워크플로우

일반 함수 노드와 LLM Agent 노드를 1열로 연결하여 단계별로 처리하는 가장 기본적인 파이프라인 그래프입니다.

---

## 1. 그래프 구조

```
[START] ──▶ parse_query ──▶ fetch_data ──▶ llm_summary (Agent) ──▶ [END]
```

- **엔트리포인트**: `agent.py`의 `root_agent` (`seq_demo`)
- **노드 간 데이터 전달**:
  - `parse_query`가 추출한 도시 정보가 다음 `fetch_data` 함수의 인자로 전달되고, 최종 데이터가 LLM 에이전트의 프롬프트로 흘러가 요약 응답을 생성합니다.

---

## 2. 실행 방법

`part09_graph_workflow` 폴더에서 실행합니다 (🔑 Gemini 키 필요):

```bash
cd part09_graph_workflow
uv run run_workflows.py seq
```


