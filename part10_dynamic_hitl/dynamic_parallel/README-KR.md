# dynamic_parallel — 동적 병렬 워커(Dynamic Parallel) 워크플로우

입력으로 주어지는 아이템 목록(예: 조사 주제 3개)의 크기에 맞춰 워커 노드를 동적으로 생성하고, 병렬로 실행하여 결과를 종합하는 실습입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **실행 흐름**:
  1. 입력: `ADK, LangGraph, AutoGen`
  2. 분할 노드가 주제 3개를 추출하고 각각을 담당할 워커 노드를 동적으로 생성
  3. `asyncio.gather` 기반으로 병렬 조사 실행 (총 12건 심층 분석)
  4. 점수 상위 항목을 추출하여 최종 요약 보고

---

## 2. 실행 방법

🟢 **LLM 키 없이 실행 가능합니다.**

```bash
cd part10_dynamic_hitl
uv run run_part10.py
```


