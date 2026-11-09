# skills_agent — SkillToolset 기반 점진적 스킬 로딩 에이전트

필요한 전문 지식과 지침을 컨텍스트에 한꺼번에 넣지 않고, 요청이 들어왔을 때만 점진적으로 로드(Lazy Loading)하는 **Skills for ADK Agents** 패턴 실습입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent` (`skill_user_agent`)
- **스킬 3단계 로딩 (컨텍스트 절약)**:
  - **L1 (메타데이터)**: `SKILL.md`의 frontmatter(`name`, `description`) → 기본 노출되어 모델이 어떤 스킬이 있는지 판단 (`list_skills`)
  - **L2 (본문 지시)**: 모델이 `load_skill`을 호출할 때 본문 지시문(`instructions`)만 로드
  - **L3 (외부 리소스)**: references/, assets/, scripts/ 등 대용량 데이터는 필요 시 `load_skill_resource`로 로드
- **스킬 구성**:
  1. **파일시스템 기반 스킬 (`weather-report`)**:
     - `skills/weather-report/SKILL.md`: frontmatter(name · description · `metadata.adk_additional_tools: [get_weather]`) + 단계별 지시문
     - `scripts/outdoor_rule.py`: 야외 활동 판단 (결정론적 코드, `run_skill_script`)
     - `references/rules.md`: 폭염·한파·조회 실패 예외 규칙 (`load_skill_resource`)
     - `assets/briefing_template.md`: 공지 형식 템플릿 (`load_skill_resource`)
  2. **코드 인메모리 정의 스킬 (`greeting-skill`)**:
     - `models.Skill` 객체로 직접 정의한 환영 인사 스킬
  3. **동적 추가 도구 (`additional_tools=[get_weather]`)**:
     - `SKILL.md`의 `metadata.adk_additional_tools`에 이름이 있어야, 스킬이 `load_skill`로 활성화된 뒤에만 노출된다 (빠뜨리면 모델이 날씨를 지어낸다)
  4. **스크립트 실행 (`code_executor=UnsafeLocalCodeExecutor()`, `script_timeout=30`)**:
     - 실습 전용. 운영에서는 샌드박스 실행기를 쓴다
- **도구 목록 (google-adk 2.6.3)**: `list_skills` · `load_skill` · `load_skill_resource` · `run_skill_script` (+ `registry=` 를 주면 `search_skills`). 최신 2.14에는 `unload_skill`, `discovery_mode`, `lifecycle_config`가 추가됐다.
- **LLM 없이 확인**: `uv run skills_explorer.py` (part05_skills 폴더)

---

## 2. 실행 방법

`part05_skills` 폴더에서 실행합니다:

```bash
cd part05_skills

# 1. 스크립트 실행 (인사 스킬 + 날씨 스킬 로딩 시연)
uv run run_skills.py

# 2. 터미널 대화형 실행
adk run skills_agent

# 3. 웹 개발 UI 실행
adk web --port 8000
```

### 질의 및 로딩 흐름 예시
```text
User: 김철수 학생 환영 인사 해줘
Agent: [load_skill('greeting-skill') 호출]
Agent: [references/hello.txt 로드]
Agent: 김철수님, Agentic AI 10주차 수업에 오신 것을 환영합니다!

User: 서울 날씨 보고서 양식대로 작성해줘
Agent: [load_skill('weather-report') 호출]
Agent: [get_weather('서울') 호출]
Agent: [보고서 양식에 맞춘 맑음, 18°C 날씨 브리핑 출력]
```


