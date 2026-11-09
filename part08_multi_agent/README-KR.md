# part08_multi_agent — 멀티 에이전트 시스템 (Multi-Agent Systems)

> 강의노트 **Part 8 · 08. 멀티에이전트 구성** (슬라이드 85–90)과 짝을 이룬다.

여러 전문 에이전트가 협업하는 핵심 아키텍처 패턴인 **Handoff(전환/이양)**, **ADK 1.x 파이프라인(순차·병렬·루프)**, 그리고 **ADK 2.0 Task 위임 패턴**을 다룹니다.

---

## 1. 폴더 구조 및 서브 에이전트

```text
part08_multi_agent/
├── help_desk/           # sub_agents 기반 동적 대화 전환 (Triage → Billing / Tech)
├── report_pipeline/     # SequentialAgent + ParallelAgent + LoopAgent (보고서 생성 파이프라인)
├── travel_planner/      # ADK 2.0 single_turn(날씨) 및 task(항공 예약) 서브에이전트 협업
├── run_multi_agent.py   # 🔑 part08 통합 러너 스크립트
└── README-KR.md            # 현재 문서
```

---

## 2. 멀티 에이전트 패턴 비교

| 서브폴더 | 핵심 구조 | 동작 방식 |
|---|---|---|
| **help_desk** | `sub_agents=[billing, tech]` | 안내원이 대화를 분류(Triage)하고 전문 서브에이전트에게 세션 제어권 핸드오프 |
| **report_pipeline** | `Sequential`, `Parallel`, `Loop` | 1.x 컨테이너 에이전트를 조합하여 조사 → 초안 작성 → 리뷰 루프 파이프라인 구성 |
| **travel_planner** | `single_turn=True`, `task` 모드 | 총괄 에이전트가 날씨는 단발성 조회하고, 항공권은 인터랙티브한 전담 Task 에이전트에 위임 |

---

## 3. 실행 방법

`part08_multi_agent` 폴더에서 실행합니다:

```bash
cd part08_multi_agent

# 전체 멀티 에이전트 순차 실행
uv run run_multi_agent.py all

# 개별 에이전트 실행
uv run run_multi_agent.py help_desk
uv run run_multi_agent.py pipeline
uv run run_multi_agent.py travel

# 대화형 실행
adk run help_desk
adk web --port 8000
```



