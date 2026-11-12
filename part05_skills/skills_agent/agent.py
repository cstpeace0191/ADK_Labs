"""강의노트 Part 5 Skills for ADK Agents (슬라이드 59 · 63~67): Skills for ADK agents — 필요할 때만 불러오는 에이전트 전문 지식.

점진적 공개(progressive disclosure) 3단계 (슬라이드 58·59):
  발견 Discovery   = L1 메타데이터: SKILL.md frontmatter 의 name · description → 항상 노출 (list_skills)
  활성화 Activation = L2 지시     : SKILL.md 본문(단계별 지시문)              → load_skill
  실행 Execution   = L3 리소스    : scripts/ · references/ · assets/           → run_skill_script · load_skill_resource

스킬 폴더 구성 (슬라이드 59·63): skills/weather-report/
  SKILL.md                     YAML 프런트매터(name, description, metadata) + 단계별 지시문
  scripts/outdoor_rule.py      결정론적 코드: 야외 활동 판단 (같은 입력 → 같은 결과)
  references/rules.md          도메인 규칙, 예외 상황 매뉴얼 (폭염·한파, 조회 실패)
  assets/briefing_template.md  재사용 템플릿 (출력 형식)

ADK 실행 중 동작 (슬라이드 66·67, google-adk 2.6.3 기준):
  - additional_tools 는 스킬 frontmatter 의 metadata.adk_additional_tools 에 이름을 적은 도구만,
    그 스킬이 load_skill 로 활성화된 뒤에 노출된다 (빠뜨리면 모델이 도구 없이 답을 지어낸다).
  - run_skill_script 는 code_executor 가 있어야 동작한다. 실습은 UnsafeLocalCodeExecutor(현재 프로세스에서 실행)를 쓴다.
    운영에서는 샌드박스 실행기(예: VertexAiCodeExecutor, 컨테이너/GKE 실행기)를 쓴다. 기본 제한 시간 script_timeout=300초.
규칙: name 은 소문자 kebab-case 64자 이하, 폴더 이름 = name, description 1024자 이하.
문서: https://adk.dev/skills/
"""
import os
import pathlib

from google.adk import Agent
from google.adk.code_executors import UnsafeLocalCodeExecutor
from google.adk.skills import load_skill_from_dir, models
from google.adk.tools import skill_toolset

SKILLS_DIR = pathlib.Path(__file__).parent / "skills"

# ① 파일시스템 스킬: SKILL.md + scripts/ · references/ · assets/
weather_skill = load_skill_from_dir(SKILLS_DIR / "weather-report")

# ② 코드로 정의한 스킬: 리소스를 메모리에 둔다
greeting_skill = models.Skill(
    frontmatter=models.Frontmatter(
        name="greeting-skill",
        description="학생에게 수업 시작 인사를 한다. 인사나 환영 메시지를 요청받을 때 사용한다.",
    ),
    instructions="1단계: references/hello.txt 를 읽는다. 2단계: 그 문장에 학생 이름을 넣어 인사한다.",
    resources=models.Resources(references={"hello.txt": "{name}님, Agentic AI 10주차 수업에 오신 것을 환영합니다!"}),
)

WEATHER = {"서울": "맑음, 18°C", "부산": "흐림, 20°C", "제주": "비, 16°C", "대구": "맑음, 35°C"}


def get_weather(city: str) -> dict:
    """도시의 현재 날씨를 조회한다.

    Args:
        city: 도시 이름 (예: "서울")
    """
    if city in WEATHER:
        return {"status": "success", "city": city, "report": WEATHER[city]}
    return {"status": "error", "error_message": f"{city} 정보 없음"}


skills = skill_toolset.SkillToolset(
    skills=[weather_skill, greeting_skill],
    additional_tools=[get_weather],           # 스킬 metadata.adk_additional_tools 로 노출
    code_executor=UnsafeLocalCodeExecutor(),  # run_skill_script 용 (실습 전용, 운영은 샌드박스)
    script_timeout=30,
)

root_agent = Agent(
    name="skill_user_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    description="스킬을 불러와 작업하는 에이전트",
    instruction="너는 학사 도우미다. 요청에 맞는 스킬이 있으면 먼저 불러온 뒤 그 지시를 정확히 따른다.",
    tools=[skills],
)
