# part09_graph_workflow — ADK 2.0 그래프 워크플로우 (Graph Workflow)

> 강의노트 **Part 9 · 09. ADK 2.0 Graph Workflow** (슬라이드 96–105)와 짝을 이룬다.

노드(Node)와 엣지(Edge)로 구성되는 방향성 그래프 기반의 결정론적 제어 흐름과 LLM 에이전트의 결합 패턴을 다룹니다.

---

## 1. 폴더 구조 및 워크플로우 목록

```text
part09_graph_workflow/
├── seq_workflow/        # 순차 실행 패턴 (START → step1 → step2 → ...)
├── route_workflow/      # 조건부 분기 패턴 (route 엣지 매핑)
├── fan_workflow/        # 병렬 분기(Fan-Out) 및 취합(Fan-In / JoinNode)
├── loop_workflow/       # 역방향 엣지(Back-Edge)를 통한 반복/재시도 루프
├── refund_workflow/     # 실무 사례 ①: 자동 환불 및 예외 심사 워크플로우
├── expense_workflow/    # 실무 사례 ②: 출장비 경비 자동 검토 및 승인 분기
├── run_workflows.py     # 🟢/🔑 part09 전체 워크플로우 통합 러너
└── README-KR.md            # 현재 문서
```

---

## 2. 그래프 기본 패턴 및 토폴로지

| 워크플로우 | 구조 (토폴로지) | 설명 |
|---|---|---|
| **seq_workflow** | `START → a → b → END` | 이전 노드의 출력이 다음 노드의 입력으로 직렬 전달 |
| **route_workflow** | `START → router → {A: node_a, B: node_b}` | `Event(route="...")` 반환값에 따라 동적 분기 |
| **fan_workflow** | `START → [worker1, worker2] → JoinNode` | 여러 작업을 병렬 실행 후 결과를 사전으로 취합 |
| **loop_workflow** | `node → check → {RETRY: node, DONE: END}` | 종료 조건 만족 시까지 이전 노드로 되돌아가는 루프 |
| **refund_workflow** | 검증 → 금액/사유 라우팅 → 환불 → LLM 안내 | 실무 전자상거래 환불 처리 파이프라인 |
| **expense_workflow**| 금액 검사 → 자동 승인 / 관리자 심사 분기 | 전형적인 기업 경비 결재 자동화 시스템 |

---

## 3. 실행 방법

`part09_graph_workflow` 폴더에서 실행합니다:

```bash
cd part09_graph_workflow

# 1. 전체 워크플로우 순차 실행 (seq를 제외한 나머지는 🟢 LLM 키 없이 즉시 실행 가능)
uv run run_workflows.py all

# 2. 개별 워크플로우 실행
uv run run_workflows.py route
uv run run_workflows.py fan
uv run run_workflows.py loop
uv run run_workflows.py refund
uv run run_workflows.py expense
uv run run_workflows.py seq       # 🔑 Gemini 키 필요

# 3. 웹 개발 UI에서 그래프 시각화 확인 (Graph 탭)
adk web --port 8000
```



