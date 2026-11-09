"""강의노트 Part 5 Skills for ADK Agents (슬라이드 58~62): google.adk.skills 를 LLM 없이 직접 써 본다 (🟢 키 불필요).

실행: python skills_explorer.py [load|validate|toolset|coding|all]   (기본 all)
  load     : L1 list_skills_in_dir → L2/L3 load_skill_from_dir → <available_skills> XML (슬라이드 59~60)
  validate : 로드 시점 검증 — 폴더 이름≠name, 대문자 name, SKILL.md 없음, description 1,024자 초과 (슬라이드 60)
  toolset  : SkillToolset 이 모델에 주는 도구 — 활성화 전/후 (adk_additional_tools 동적 노출, 슬라이드 61~62)
  coding   : 코딩 에이전트용 스킬(~/.agents/skills 등)도 같은 SKILL.md 형식이라 ADK 로더로 읽힌다 (슬라이드 57·67)

버전 메모: 실습 환경 google-adk 2.6.3 기준. 최신(2.14)에만 있는 이름(load_skills_from_dir, unload_skill,
discovery_mode, lifecycle_config)은 있으면 쓰고, 없으면 '없음'으로 표시한다.
"""
import asyncio
import os
import pathlib
import sys
import tempfile
import textwrap
from types import SimpleNamespace

import _path  # noqa: F401  (루트 경로 + .env)
import google.adk
from google.adk import skills as adk_skills
from google.adk.skills import list_skills_in_dir, load_skill_from_dir

HERE = pathlib.Path(__file__).resolve().parent
SKILLS_DIR = HERE / "skills_agent" / "skills"


def line(title: str) -> None:
    print(f"\n{'=' * 8} {title} {'=' * 8}")


# ------------------------------------------------------------------ load
def demo_load() -> None:
    line("L1: list_skills_in_dir — frontmatter 만 읽는다")
    metas = list_skills_in_dir(SKILLS_DIR)
    for skill_id, fm in metas.items():
        print(f"  {skill_id}: name={fm.name!r}, description {len(fm.description)}자, metadata={fm.metadata}")

    line("L2 + L3: load_skill_from_dir — 본문과 리소스까지 Skill 객체로")
    skill = load_skill_from_dir(SKILLS_DIR / "weather-report")
    print(f"  name          : {skill.name}")
    print(f"  instructions  : {len(skill.instructions)}자 (L2, load_skill 때 모델에 들어감)")
    res = skill.resources
    print(f"  references/   : {res.list_references()}")
    print(f"  assets/       : {res.list_assets()}")
    print(f"  scripts/      : {res.list_scripts()}")
    first_ref = res.list_references()[0]
    print(f"  get_reference({first_ref!r}) → {res.get_reference(first_ref)[:60]!r}...")

    line("L1 목록을 모델에 보여 줄 때의 모양: <available_skills> XML")
    try:
        from google.adk.skills.prompt import format_skills_as_xml
        print(textwrap.indent(format_skills_as_xml([skill.frontmatter]), "  "))
    except ImportError:
        print("  (이 버전에는 format_skills_as_xml 이 없음)")

    print("\n  버전별 공개 API:", len(adk_skills.__all__), "개 (2.6.3 = 10, 2.14.0 = 16)")
    for name in ("load_skills_from_dir", "load_skill_from_dir_async"):
        print(f"   - {name}: {'있음' if hasattr(adk_skills, name) else '없음 (최신 버전 기능)'}")


# ------------------------------------------------------------------ validate
def _make_skill(root: pathlib.Path, folder: str, frontmatter: str | None) -> pathlib.Path:
    d = root / folder
    d.mkdir(parents=True)
    if frontmatter is not None:
        (d / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n본문 지시문\n", encoding="utf-8")
    return d


def demo_validate() -> None:
    line("로드 시점 검증: 잘못된 스킬은 에이전트 시작 전에 실패한다")
    cases = [
        ("정상", "good-skill", "name: good-skill\ndescription: 정상 스킬"),
        ("폴더 이름 ≠ name", "weather", "name: weather-report\ndescription: 이름 불일치"),
        ("name 에 대문자·밑줄", "Weather_Report", "name: Weather_Report\ndescription: kebab-case 위반"),
        ("SKILL.md 없음", "empty-skill", None),
        ("description 1,024자 초과", "long-skill", "name: long-skill\ndescription: " + "가" * 1025),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        for label, folder, fm in cases:
            d = _make_skill(root, folder, fm)
            try:
                s = load_skill_from_dir(d)
                print(f"  ✔ {label:<22} → 로드 성공: {s.name}")
            except Exception as e:  # noqa: BLE001  (교육용: 예외 종류와 메시지를 그대로 보여 준다)
                if hasattr(e, "errors"):  # pydantic ValidationError: 어느 필드가 왜 틀렸는지
                    err = e.errors()[0]
                    msg = f"{'.'.join(map(str, err['loc']))}: {err['msg']}"[:90]
                else:
                    msg = str(e).replace(str(root), "<tmp>").splitlines()[0][:90]
                print(f"  ✘ {label:<22} → {type(e).__name__}: {msg}")


# ------------------------------------------------------------------ toolset
async def demo_toolset() -> None:
    line("SkillToolset 이 모델에 주는 도구: 활성화 전 → 후")
    sys.path.insert(0, str(HERE))
    from skills_agent.agent import root_agent, skills as toolset  # 실습 에이전트의 SkillToolset 그대로

    before = await toolset.get_tools(None)
    print(f"  활성화 전 : {[t.name for t in before]}")

    # load_skill 이 하는 일: State 의 _adk_activated_skill_<에이전트 이름> 에 스킬 이름을 기록
    key = f"_adk_activated_skill_{root_agent.name}"
    ctx = SimpleNamespace(agent_name=root_agent.name, invocation_id="demo-1",
                          state={key: ["weather-report"]})
    after = await toolset.get_tools(ctx)
    print(f"  State[{key!r}] = ['weather-report'] 일 때")
    print(f"  활성화 후 : {[t.name for t in after]}")
    print("  → get_weather 는 SKILL.md 의 metadata.adk_additional_tools 에 적혀 있어서, 스킬 활성화 뒤에만 노출된다")
    print("    (metadata 에서 빼면 모델은 get_weather 를 보지 못하고 날씨를 지어낸다)")

    names = {t.name for t in after}
    for n in ("search_skills", "unload_skill"):
        note = "registry= 를 줄 때만" if n == "search_skills" else "2.14 이후"
        print(f"  {n:<14}: {'있음' if n in names else '없음'} ({note})")
    import inspect
    params = inspect.signature(type(toolset).__init__).parameters
    for p in ("discovery_mode", "lifecycle_config"):
        print(f"  SkillToolset({p}=…): {'지원' if p in params else '미지원 — 최신(2.14) 기능'}")


# ------------------------------------------------------------------ coding agents' skills
def demo_coding() -> None:
    line("코딩 에이전트용 스킬도 같은 SKILL.md 형식 → ADK 로더로 읽힌다")
    import logging
    logging.getLogger().setLevel(logging.ERROR)  # SKILL.md 없는 폴더는 경고 후 건너뛴다(조용히)
    home = pathlib.Path.home()
    places = {
        "정본 (npx skills -g)": home / ".agents" / "skills",
        "Claude Code": home / ".claude" / "skills",
        "Antigravity (App·IDE)": home / ".gemini" / "config" / "skills",
        "Antigravity CLI": home / ".gemini" / "antigravity-cli" / "skills",
    }
    for label, path in places.items():
        if not path.is_dir():
            print(f"  {label:<22} {path}  (없음)")
            continue
        try:
            metas = list_skills_in_dir(path)
        except Exception as e:  # noqa: BLE001
            print(f"  {label:<22} {path}  읽기 실패: {type(e).__name__}: {e}")
            continue
        adk = sorted(k for k in metas if k.startswith("google-agents-cli"))
        print(f"  {label:<22} {path}  스킬 {len(metas)}개, 그중 google-agents-cli-* {len(adk)}개")
    print("  설치: uvx google-agents-cli setup  (자세히: part12_agents_cli/coding_with_ai/README-KR.md)")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    print(f"google-adk {google.adk.__version__}")
    if mode in ("load", "all"):
        demo_load()
    if mode in ("validate", "all"):
        demo_validate()
    if mode in ("toolset", "all"):
        asyncio.run(demo_toolset())
    if mode in ("coding", "all"):
        demo_coding()


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    main()
