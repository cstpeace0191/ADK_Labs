# help_desk — 고객센터 대화 이양(Handoff) 멀티 에이전트

고객의 문의 사항에 따라 최적의 전담 에이전트로 제어권을 전환(Transfer)하는 계층적 헬프데스크 시스템입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent` (`triage_agent`)
- **서브 에이전트 목록**:
  - `billing_agent`: 결제 실패 원인 조회, 환불 규정 안내
  - `tech_agent`: 앱 튕김, 로그인 오류, 네트워크 기술 지원
- **동작 방식**:
  - 사용자가 `INV-2026-001 결제가 왜 실패했죠?`라고 묻는 즉시 안내원(`triage_agent`)이 `billing_agent`에게 대화를 전환합니다.
  - 이후 결제 관련 대화는 `billing_agent`가 이어받아 처리하며, 사용자가 기술 문제를 언급하면 다시 `tech_agent`로 유연하게 핸드오프됩니다.

---

## 2. 실행 방법

`part08_multi_agent` 폴더에서 실행합니다:

```bash
cd part08_multi_agent
uv run run_multi_agent.py help_desk
```


