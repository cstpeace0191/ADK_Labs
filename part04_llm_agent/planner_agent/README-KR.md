# planner_agent — 사고 과정(Thinking) 제어 플래너 에이전트

Gemini의 사고 과정(Thought / Chain-of-Thought) 제어 및 ReAct 방식의 계획 유도를 지원하는 플래너 설정 에이전트입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent` (`thinker`)
- **주요 구성**:
  1. **`BuiltInPlanner`**: 모델 자체의 Thinking 기능 활성화
     ```python
     planner = BuiltInPlanner(
         thinking_config=types.ThinkingConfig(
             include_thoughts=True,
             thinking_level="low",  # minimal | low | medium | high
         )
     )
     ```
  2. **`PlanReActPlanner`**:
     프롬프트 레벨에서 `/*PLANNING*/`, `/*ACTION*/` 태그 생성을 유도하여 계획 및 행동 패턴을 구조화합니다.

---

## 2. 실행 방법

`part04_llm_agent` 폴더에서 실행합니다:

```bash
cd part04_llm_agent
uv run run_with_runner.py planner
```

### 기대 출력 예시
```text
(thought) 문제를 해결하기 위해 먼저 배포 절차의 각 단계를 나열하고 우선순위를 정해야 한다...
final: 소프트웨어 배포 절차는 1단계 빌드, 2단계 단위 테스트, 3단계 배포 순서로 진행됩니다.
```


