# step5_hitl_retry — 5단계: 성적 정정 HITL 승인 게이트 및 재시도

성적 정정과 같이 중요한 학사 변경 요청을 접수했을 때 교수의 승인을 기다리는 HITL 게이트와 전산망 오류 시 재시도 로직을 결합한 워크플로우입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **핵심 기능**:
  - `RequestInput`: 학생의 성적 정정 사유와 과목명을 받아 담당 교수 승인 폼(`adk_request_input`)으로 전환
  - 교수가 승인(`approve: True`)하면 학사 DB 반영 노드로 이동, 거절 시 사유 안내
  - DB 반영 시 일시적 연결 오류 발생 시 최대 3회 자동 재시도(Retry)

---

## 2. 실행 방법

🟢 **LLM 키 없이 오프라인에서 즉시 실행 가능합니다.**

```bash
cd part13_lab
uv run run_lab.py 5
```


