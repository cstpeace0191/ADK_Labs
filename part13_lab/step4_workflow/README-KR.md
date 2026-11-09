# step4_workflow — 4단계: 학사 문의 라우팅 그래프 워크플로우

단일 에이전트 대신 질의의 의도를 분석하여 성적 조회, 수강 조회, 일반 학사 규정 응답 노드로 결정론적으로 분기하는 그래프 워크플로우입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent` (`academic_workflow`)
- **그래프 분기 흐름**:
  - `classify_intent`: 사용자 질의를 `GRADES`, `COURSES`, `GENERAL`로 분류
  - 분류 결과에 따라 전담 함수 노드로 즉시 라우팅되어 신속하고 정확한 데이터 반환

---

## 2. 실행 방법

🟢 **LLM 키 없이 오프라인에서 즉시 실행 가능합니다.**

```bash
cd part13_lab
uv run run_lab.py 4
```


