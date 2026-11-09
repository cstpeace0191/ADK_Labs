# part04_llm_agent — LLM Agent 심화 기능

> 강의노트 **Part 4 · 04. LLM Agent 프로그래밍** (슬라이드 44–51)과 짝을 이룬다.

Google ADK의 `Agent` 핵심 구성 요소인 **도구 연동**, **프롬프트 템플릿(State 치환)**, **구조화 출력(`output_schema`)**, **모델 사고 설정(`Planner`)**, **타 공급자 모델 연동(`LiteLLM`)**을 다룹니다.

---

## 1. 폴더 구조 및 에이전트 목록

```text
part04_llm_agent/
├── weather_agent/     # 도구 호출 및 세션 State 연동
├── tutor_agent/       # 프롬프트 템플릿 내 세션 변수 치환 ({user:name}, {course})
├── reviewer_agent/    # Pydantic 기반 구조화 출력 강제 및 state['review'] 저장
├── planner_agent/     # BuiltInPlanner(사고 과정 노출) 및 PlanReActPlanner
├── litellm_agent/     # LiteLLM을 통한 타 모델 공급자(Anthropic Claude 등) 연동
├── run_with_runner.py # 🔑 통합 실행 러너 스크립트
└── README-KR.md          # 현재 문서
```

---

## 2. 에이전트별 핵심 개념

| 에이전트 | 핵심 ADK 기능 | 특징 |
|---|---|---|
| **weather_agent** | 일반 함수 도구 연동 | 함수 시그니처와 독스트링 기반 자동 스키마 변환 |
| **tutor_agent** | State 템플릿 치환 | 지시문 내 `{user:name}` 형태로 세션 상태 변수 주입 |
| **reviewer_agent** | `output_schema`, `output_key` | Pydantic 모델로 응답 JSON 강제 및 `state['review']` 자동 저장 |
| **planner_agent** | `BuiltInPlanner`, `PlanReActPlanner` | Gemini Thinking 설정 (`include_thoughts=True`) |
| **litellm_agent** | `LiteLlm` 어댑터 | Gemini 외 Claude 등 이종 LLM 교체 실행 |

---

## 3. 실행 방법

### ① 통합 러너 실행 (🔑 Gemini 키 필요)
`part04_llm_agent` 폴더에서 `run_with_runner.py`를 실행합니다:

```bash
cd part04_llm_agent

# 전체 에이전트 순차 실행
uv run run_with_runner.py all

# 특정 에이전트만 개별 실행
uv run run_with_runner.py weather
uv run run_with_runner.py tutor
uv run run_with_runner.py reviewer
uv run run_with_runner.py planner
uv run run_with_runner.py litellm
```

### ② 대화형 인터페이스 (`adk web` / `adk run`)
```bash
# 원하는 에이전트 지정하여 REPL 실행
adk run weather_agent
adk run reviewer_agent

# 웹 UI에서 에이전트 선택 실행 (http://localhost:8000)
adk web --port 8000
```



