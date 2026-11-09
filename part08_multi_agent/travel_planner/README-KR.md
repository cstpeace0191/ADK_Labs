# travel_planner — ADK 2.0 Task 위임 여행 플래너

총괄 기획 에이전트가 단발성 조회(`single_turn`)와 인터랙티브한 다단계 작업(`task` 서브에이전트)을 분리하여 지능적으로 조율하는 실습입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent` (`planner`)
- **서브 에이전트 구조**:
  - `weather_scout` (`single_turn=True`): 제주도 여행 날짜의 날씨만 단발성으로 확인하고 즉시 부모에게 복귀
  - `flight_agent` (Task 모드): 사용자에게 원하는 좌석(창가/복도), 시간대(오전/오후)를 되물어보며 항공권 예약을 완수하는 독립 대화 태스크 수행

---

## 2. 실행 방법

`part08_multi_agent` 폴더에서 실행합니다:

```bash
cd part08_multi_agent
uv run run_multi_agent.py travel
```


