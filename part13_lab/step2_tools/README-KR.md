# step2_tools — 2단계: 학사 DB 도구 연동 에이전트

학생 개인의 성적 조회 및 수강 신청 내역 조회를 위한 파이썬 함수 도구를 에이전트에 연동한 단계입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **추가된 도구**:
  - `get_grades(student_id)`: 특정 학생의 과목별 취득 학점(A+, B0 등) 조회
  - `get_courses(student_id)`: 이번 학기 수강 신청한 과목 목록 조회

---

## 2. 실행 방법

`part13_lab` 폴더에서 실행합니다 (🔑 Gemini 키 필요):

```bash
cd part13_lab
uv run run_lab.py 2
```


