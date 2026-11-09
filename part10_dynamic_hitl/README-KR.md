# part10_dynamic_hitl — 동적 워크플로우, HITL 및 재시도 (Dynamic, HITL & Retry)

> 강의노트 **Part 10 · 10. Dynamic · HITL · Retry** (슬라이드 101–109)와 짝을 이룬다.

실행 시점에 그래프 형상이 동적으로 결정되는 **동적 노드/병렬 처리**, 사람의 개입을 안전하게 처리하는 **Human-in-the-Loop (HITL)**, 그리고 일시적 장애를 복구하는 **재시도(Retry)** 패턴을 다룹니다.

---

## 1. 폴더 구조 및 워크플로우 목록

```text
part10_dynamic_hitl/
├── dynamic_workflow/    # 런타임에 동적으로 노드를 생성하여 실행
├── dynamic_parallel/    # 입력 개수(배열)에 따라 가변 개수의 워커를 동적 병렬 실행
├── hitl_workflow/       # RequestInput 기반 사람 입력 대기 및 중단/재개 기본 패턴
├── feedback_workflow/   # 추천 결과를 사람에게 보여주고 피드백(선호/수정)을 받아 반영
├── approval_gate/       # 고위험 작업(환불 승인 등)의 결재 게이트 및 감사(Audit) 로그
├── retry_workflow/      # 일시적 네트워크 실패에 대한 점진적 재시도(Retry) 정책
├── run_part10.py        # 🟢 part10 전체 워크플로우 오프라인 통합 러너
└── README-KR.md            # 현재 문서
```

---

## 2. HITL 및 동적 패턴 핵심 메커니즘

| 워크플로우 | 핵심 메커니즘 | 설명 |
|---|---|---|
| **dynamic_workflow** | 런타임 그래프 확장 | 고정되지 않은 작업 단계 수만큼 동적으로 노드를 연결하여 실행 |
| **dynamic_parallel** | 동적 팬아웃 | `gather` 패턴으로 입력된 N개의 토픽에 대해 N개의 분석 워커를 동시 구동 |
| **hitl_workflow** | `RequestInput` | `adk_request_input` 이벤트를 내며 실행을 멈추고 외부 입력 수신 후 재개 |
| **feedback_workflow** | 인터랙티브 피드백 | 사용자에게 후보군 payload를 제시하고, 사용자의 선택/코멘트에 따라 최종 일정 확정 |
| **approval_gate** | 관리자 승인 게이트 | 승인(`approve: True`) 또는 거절(`approve: False`)과 사유를 받아 감사 추적 |
| **retry_workflow** | 예외 재시도 정책 | 1, 2회차 네트워크 에러 시 백오프 대기 후 3회차에 자동 성공 복구 |

---

## 3. 실행 방법

`part10_dynamic_hitl` 폴더에서 실행합니다:

```bash
cd part10_dynamic_hitl

# 1. 전체 실습 순차 실행 (🟢 LLM API 키 없이 오프라인에서 즉시 실행)
uv run run_part10.py

# 2. 웹 UI에서 대화형 HITL 폼 직접 체험 (http://localhost:8000)
adk web --port 8000
```



