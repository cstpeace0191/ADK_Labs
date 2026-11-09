# part05_skills — Skills for ADK Agents

> 강의노트 **Part 5 · 05. Skills for ADK Agents** (슬라이드 52–69)와 짝을 이룬다.
> SKILL.md · 점진적 공개 · SkillToolset · google.adk.skills · Agents CLI 스킬

ADK 에이전트가 **실행 중에 쓰는 스킬**(SkillToolset)을 다룬다. 코딩 에이전트(Claude Code · Antigravity)가 ADK 코드를 **만들 때 쓰는 스킬**(google-agents-cli-*, 슬라이드 63–68)의 설치·연결은 [`../part12_agents_cli/coding_with_ai/`](../part12_agents_cli/coding_with_ai/README-KR.md)에 있다.

---

## 1. 폴더 구조

```text
part05_skills/
├── skills_agent/                    # SkillToolset 에이전트 (root_agent = skill_user_agent)
│   ├── agent.py                     # 파일 스킬 + 코드 스킬 + additional_tools + code_executor
│   └── skills/weather-report/
│       ├── SKILL.md                 # frontmatter(name · description · metadata.adk_additional_tools) + 지시문
│       ├── scripts/outdoor_rule.py  # L3: 결정론적 코드 (run_skill_script)
│       ├── references/rules.md      # L3: 예외 규칙 (load_skill_resource)
│       └── assets/briefing_template.md
├── skills_explorer.py               # 🟢 google.adk.skills 오프라인 탐색 (LLM 없음)
├── run_skills.py                    # 🔑 스킬 에이전트 실행 러너
└── README-KR.md
```

## 2. 슬라이드와 코드

| 슬라이드 | 내용 | 코드 |
|---|---|---|
| 53–54 | 에이전트 스킬, SKILL.md 폴더 · L1→L2→L3 | `skills_agent/skills/weather-report/` |
| 57 | 코딩 도구의 Skills vs ADK Skills | 이 폴더 = ADK Skills, 코딩 도구 스킬은 `part12_agents_cli/coding_with_ai/` |
| 58 | ADK Skills 구조: SkillToolset 연결 | `skills_agent/agent.py` |
| 59–60 | google.adk.skills 모듈 · `load_skill_from_dir()` 처리 흐름 · 검증 | `skills_explorer.py load` · `validate` |
| 61–62 | 런타임 구조 · 실행 중 동작(활성화 기록, 도구 동적 노출) | `skills_explorer.py toolset` · `run_skills.py` |
| 67 | 코딩 에이전트에 ADK 스킬 설치 | `skills_explorer.py coding` (설치 확인) |

## 3. 실행 (part05_skills 폴더에서)

```bash
cd part05_skills

# 🟢 LLM 없이: 로드 · 검증 · 도구 노출 · 코딩 에이전트 스킬
uv run skills_explorer.py                 # all
uv run skills_explorer.py validate        # load | validate | toolset | coding

# 🔑 Gemini 키 필요: 발견 → 활성화 → 실행
uv run run_skills.py                      # weather | greeting | all
adk run skills_agent               # 터미널 대화
adk web --port 8000                # 개발 UI (Events 탭에서 load_skill · get_weather 호출 확인)
```

## 4. google-adk 2.6.3 (실습 환경) 기준 주의

- 모델이 받는 도구: `list_skills` · `load_skill` · `load_skill_resource` · `run_skill_script` (+ `registry=` 를 주면 `search_skills`).
  최신 2.14에는 `unload_skill`, `SkillToolset(discovery_mode=…, lifecycle_config=…)`가 추가됐다.
- `additional_tools`로 넘긴 도구(`get_weather`)는 SKILL.md의 `metadata.adk_additional_tools`에 이름이 있어야, 스킬이 활성화된 뒤에만 노출된다. 빠뜨리면 모델이 날씨를 지어낸다.
- `run_skill_script`는 `code_executor`가 있어야 동작한다. 실습은 `UnsafeLocalCodeExecutor`(현재 프로세스), 운영은 샌드박스 실행기를 쓴다.
- 스킬 규칙: name은 소문자 kebab-case 64자 이하, **폴더 이름 = name**, description 1,024자 이하 (`skills_explorer.py validate`로 확인).
