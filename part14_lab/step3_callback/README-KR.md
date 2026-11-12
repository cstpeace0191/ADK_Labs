# step3_callback — 3단계: 개인정보 보호 가드레일 에이전트

학생들이 대화창에 주민등록번호나 비밀번호 등 민감 정보를 입력했을 때, LLM 호출 전에 선제적으로 감지하고 차단하는 가드레일 단계입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **가드레일 로직 (`guardrails.py`)**:
  - `before_model_callback`: 주민등록번호 정규식(`\d{6}-\d{7}`) 패턴이 매칭되면 즉시 `"개인정보(주민등록번호)는 입력하지 마세요."`라는 `LlmResponse`를 반환하고 LLM API 요청을 취소합니다.

---

## 2. 실행 방법

`part14_lab` 폴더에서 실행합니다:

```bash
cd part14_lab
uv run run_lab.py 3
```


