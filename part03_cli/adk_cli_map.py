"""강의노트 Part 3 슬라이드 32–36: adk CLI 동작 구조를 소스에서 직접 확인한다. 🟢 키 없이 실행.

실행 (part03_cli 폴더): python adk_cli_map.py [commands|loader|services|routes|all]
  commands : cli_tools_click.main 의 Click 명령 트리 (슬라이드 32)
  loader   : AgentLoader 가 my_agent 를 찾아 돌려주는 객체 (슬라이드 34)
  services : service_registry 에 등록된 URI scheme (슬라이드 34)
  routes   : get_fast_api_app(web=False/True) 가 만드는 경로 수 — api_server vs web (슬라이드 35–36)
"""
import logging
import sys
from pathlib import Path

import _path  # noqa: F401

logging.disable(logging.WARNING)
HERE = Path(__file__).resolve().parent


def section(t: str) -> None:
    print(f"\n=== {t} ===")


def commands() -> None:
    import click
    from google.adk.cli.cli_tools_click import main
    section("commands: adk = cli_tools_click.main (Click group)")
    ctx = click.Context(main)

    def walk(group, prefix="adk"):
        for name in sorted(group.list_commands(ctx)):
            cmd = group.get_command(ctx, name)
            if isinstance(cmd, click.Group):
                subs = " · ".join(sorted(cmd.list_commands(ctx)))
                print(f"  {prefix} {name:<12} → {{ {subs} }}")
            else:
                print(f"  {prefix} {name:<12} → {cmd.callback.__module__.split('.')[-1]}.{cmd.callback.__name__}()")
    walk(main)


def loader() -> None:
    from google.adk.cli.utils.agent_loader import AgentLoader
    section("loader: AgentLoader(agents_dir=part03_cli).load_agent('my_agent')")
    obj = AgentLoader(agents_dir=str(HERE)).load_agent("my_agent")
    print(f"  type={type(obj).__name__}  name={obj.name}")
    print("  찾는 순서: my_agent/agent.py → my_agent.py · __init__.py → root_agent.yaml (app 이 있으면 app 우선)")


def services() -> None:
    from google.adk.cli.service_registry import get_service_registry
    section("services: --*_service_uri 의 scheme → 팩토리")
    reg = get_service_registry()
    for kind in ("session", "artifact", "memory"):
        schemes = sorted(getattr(reg, f"_{kind}_factories"))
        print(f"  {kind:<9} {' · '.join(s + '://' for s in schemes)}")


def routes() -> None:
    from google.adk.cli.fast_api import get_fast_api_app
    section("routes: get_fast_api_app(web=False) = api_server · web=True = adk web")
    counts = {}
    for web in (False, True):
        app = get_fast_api_app(agents_dir=str(HERE), web=web, use_local_storage=False,
                               session_service_uri="memory://", artifact_service_uri="memory://")
        paths = sorted({getattr(r, "path", "") for r in app.routes} - {""})
        counts[web] = paths
        dev = [p for p in paths if p.startswith("/dev")]
        print(f"  web={web!s:<5} 경로 {len(paths):>2}개 (/dev/* {len(dev)}개) · 실행: {[p for p in paths if p.startswith('/run')]}")
    only_web = sorted(set(counts[True]) - set(counts[False]))
    print(f"  web에만 있는 경로 예: {only_web[:4]} …")


ITEMS = {"commands": commands, "loader": loader, "services": services, "routes": routes}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for k, fn in ITEMS.items():
        if which in (k, "all"):
            fn()
