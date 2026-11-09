# chat_time_weather_agent — 시간·날씨 및 일반 대화 에이전트

`chat_time_weather_agent`는 Google ADK 기반으로 세계 도시의 현재 시각 및 실시간 기상 정보를 제공하고, 일반적인 대화 및 질의응답도 수행할 수 있는 범용 비서 에이전트입니다.

> **💡 폴더명 안내**:
> Python 표준 문법(PEP 8) 및 Google ADK의 `AgentLoader` 규격(`^[a-zA-Z0-9_]+$`)에 따라, 하이픈(`-`) 대신 언더스코어(`_`)를 사용한 **`chat_time_weather_agent`** 단일 폴더로 구성되어 있습니다. (`import` 문법 오류 및 `adk run` 로딩 실패 방지)

---

## 1. 주요 기능 및 동작 구조

1. **지오코딩 (`geocode`)**:
   - Open-Meteo Geocoding API를 호출하여 도시/지역명을 위도, 경도, IANA 시간대(예: `Asia/Seoul`, `America/New_York`, `Europe/Paris`)로 변환합니다.
   - 한국어 주요 도시명(서울, 부산, 제주, 도쿄, 뉴욕 등) 사전 매핑과 오프라인 백업 데이터를 내장하여 높은 안정성을 제공합니다.
2. **실시간 현지 시각 조회 (`get_current_time`)**:
   - `geocode`로 도출된 표준 시간대를 바탕으로 Python `zoneinfo.ZoneInfo`를 적용하여 해당 도시의 실제 현지 시각(UTC 오프셋 포함)을 계산합니다.
3. **실시간 기상 정보 조회 (`get_weather`)**:
   - Open-Meteo Forecast API를 호출하여 현재 날씨 상태(WMO 코드 해석), 기온, 체감 온도, 상대 습도, 풍속을 실시간으로 가져옵니다.
4. **일반 대화 및 상식 질의응답 (General Chat)**:
   - 시간/날씨 조회가 필요 없는 일반 대화(인사, 상식 질의, 프로그래밍, 요약 등)에는 외부 도구를 호출하지 않고 LLM이 직접 자연스럽게 답변합니다.

---

## 2. 파일 구성

```text
chat_time_weather_agent/
├── __init__.py           # agent 모듈 및 root_agent 노출
├── agent.py              # geocode, get_current_time, get_weather 도구 및 root_agent 정의
└── README-KR.md          # 현재 설명서 문서
```

---

## 3. 실행 방법

`part02_architecture` 폴더에서 실행합니다:

```bash
cd part02_architecture

# ① 터미널 REPL 대화 실행
adk run chat_time_weather_agent

# ② 웹 개발 UI 실행
adk web --port 8008

# ③ 이벤트 생명주기 관찰 스크립트 실행
uv run run_events.py
```

---

## 4. 대화 예시

### ① 시간 및 날씨 질의 (도구 자동 호출)
```text
User: 뉴욕 지금 몇 시고 날씨 어때?
Agent: [도구 geocode / get_current_time / get_weather 호출]
Agent: 현재 미국 뉴욕의 현지 시각은 2026-11-09 17:55 EST (UTC-0500)이며,
       날씨는 맑음, 기온은 11.3°C (체감 온도 10.8°C), 습도 42% 입니다.
```

### ② 일반 질문 (도구 호출 없이 직접 답변)
```text
User: 파이썬에서 데코레이터가 뭐야?
Agent: 파이썬에서 데코레이터(Decorator)는 기존 함수의 코드를 직접 수정하지 않고 기능을 확장하거나 변경할 수 있도록 해주는 문법 요소입니다...
```
