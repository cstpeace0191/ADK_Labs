# weather_agent — 평가 대상 날씨 에이전트 및 벤치마크 데이터셋

`adk eval` 및 `AgentEvaluator`의 평가 대상이 되는 에이전트와 골든 데이터셋(`weather.evalset.json`), 평가 설정(`test_config.json`)을 포함합니다.

---

## 1. 파일 구성

- `agent.py`: 날씨 조회 도구(`get_weather`)를 가진 에이전트 정의
- `weather.evalset.json`:
  - 평가 케이스 모음 (예: "서울 날씨?", "제주 날씨?")
  - 각 케이스별 기대 도구 호출 목록(`expected_tool_calls`) 및 기대 응답(`expected_responses`)
- `test_config.json`:
  - 평가 지표 설정 (`tool_trajectory_evaluator`, `response_evaluator`)
  - 임계값(Threshold) 및 가중치 지정

---

## 2. 평가 실행 방법

`part11_eval_deploy` 상위 폴더에서 실행합니다:

```bash
cd part11_eval_deploy
adk eval weather_agent weather_agent/weather.evalset.json --config_file_path weather_agent/test_config.json --print_detailed_results
```

