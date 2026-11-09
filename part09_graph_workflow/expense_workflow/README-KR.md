# expense_workflow — 실무 사례 ②: 출장비 경비 심사 워크플로우

기업 출장비 청구 내역(영수증 금액, 항목)을 분석하여 자동 전결 및 부서장 결재 분기를 처리하는 워크플로우입니다.

---

## 1. 비즈니스 흐름

1. **영수증 검토 (`audit_receipt`)**: 적격 증빙 여부 확인
2. **사내 전결 규정 분기 (`check_limit`)**:
   - 20만 원 이하: 자동 승인(Auto-Approved) 및 회계 시스템 전송
   - 20만 원 초과: 사유서 요구 및 부서장 결재(Needs Review) 분기
3. **최종 정산 리포트 생성**

---

## 2. 실행 방법

🟢 **LLM 키 없이 실행 가능합니다.**

```bash
cd part09_graph_workflow
uv run run_workflows.py expense
```


