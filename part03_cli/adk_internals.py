"""강의노트 Part 3 슬라이드 31~38: adk CLI 가 대신 해 주는 일을 ADK 내부 코드로 그대로 재현한다.

`adk run my_agent` 를 실행하면 adk 는 다음 5단계를 거친다 (google.adk.cli.cli._setup_runner_context, ADK 2.6.3).
  ① 찾기       AgentLoader 가 my_agent 폴더에서 app → root_agent 순으로 찾는다
  ② .env 로드   에이전트 폴더부터 위로 올라가며 .env 를 찾는다 (그래서 실습 루트 .env 하나로 충분)
  ③ 서비스 생성  --session_service_uri 등 URI 플래그 · 없으면 로컬 .adk 저장소 (세션 = .adk/session.db, SQLite)
  ④ Runner 생성  Runner(app=…, session_service=…, artifact_service=…, memory_service=…)
  ⑤ 입구 제공    run: 터미널 input() 루프 · web/api_server: HTTP 요청마다 run_async()

실행 (part03_cli 폴더):
  python adk_internals.py                       🟢 ①~④ 만 (LLM 호출 없음)
  python adk_internals.py --in_memory            🟢 adk run --in_memory 와 같은 서비스 선택
  python adk_internals.py --session_service_uri sqlite:///tmp_sessions.db
  python adk_internals.py --ask "서울 날씨?"      🔑 ⑤ 까지: adk run 의 한 턴과 같은 동작

주의: google.adk.cli.utils 는 ADK 내부 API 라 버전마다 바뀔 수 있다 (학습용 재현).
     기본(로컬 저장소) 모드는 실제 adk run 처럼 my_agent/.adk/ 폴더를 만든다.
"""
import argparse
import asyncio
from pathlib import Path

import _path  # noqa: F401
from google.adk.cli.cli import _to_app
from google.adk.cli.utils import envs
from google.adk.cli.utils.agent_loader import AgentLoader
from google.adk.cli.utils.service_factory import (
    create_artifact_service_from_options,
    create_memory_service_from_options,
    create_session_service_from_options,
)
from google.adk.runners import Runner
from google.genai import types

AGENTS_DIR = Path(__file__).resolve().parent  # = adk run 을 실행하는 상위 폴더
AGENT = "my_agent"


async def main(a: argparse.Namespace) -> None:
    # ① 찾기
    agent_or_app = AgentLoader(agents_dir=str(AGENTS_DIR)).load_agent(AGENT)
    print(f"① 찾기       AgentLoader → {type(agent_or_app).__name__} name={agent_or_app.name!r}"
          f" (from {AGENT}/agent.py)")

    # ② .env 로드
    envs.load_dotenv_for_agent(AGENT, str(AGENTS_DIR))
    import os
    print(f"② .env 로드   GOOGLE_API_KEY 설정됨={bool(os.getenv('GOOGLE_API_KEY'))}"
          f" · ADK_MODEL={os.getenv('ADK_MODEL', '(기본)')}")

    # ③ 서비스 생성 (adk run 과 같은 함수, 같은 기본값)
    session_uri = "memory://" if a.in_memory else a.session_service_uri
    use_local = not a.in_memory
    ss = create_session_service_from_options(base_dir=AGENTS_DIR, session_service_uri=session_uri,
                                             use_local_storage=use_local)
    arts = create_artifact_service_from_options(base_dir=AGENTS_DIR,
                                                artifact_service_uri="memory://" if a.in_memory else None,
                                                use_local_storage=use_local)
    mem = create_memory_service_from_options(base_dir=AGENTS_DIR, memory_service_uri=None)
    where = {"PerAgentDatabaseSessionService": f"→ {AGENT}/.adk/session.db (SQLite, 첫 세션 때 생성)",
             "SqliteSessionService": f"→ {getattr(ss, '_db_path', '')}",
             "InMemorySessionService": "→ 프로세스 메모리 (종료하면 소멸)"}.get(type(ss).__name__, "")
    print(f"③ 서비스 생성  session={type(ss).__name__} {where}")
    print(f"              artifact={type(arts).__name__} · memory={type(mem).__name__}")

    # ④ Runner 생성
    app = _to_app(agent_or_app, AGENT)
    runner = Runner(app=app, session_service=ss, artifact_service=arts, memory_service=mem)
    print(f"④ Runner 생성  Runner(app={app.name!r}, root_agent={app.root_agent.name!r})")

    # ⑤ 입구 제공
    if not a.ask:
        print("⑤ 입구 제공   adk run 이면 여기서 input('[user]: ') 루프 → runner.run_async()"
              "\n              (--ask \"질문\" 을 주면 한 턴을 실제로 실행한다)")
        return
    session = await ss.create_session(app_name=AGENT, user_id="test_user")
    print(f"⑤ 입구 제공   [user]: {a.ask}")
    async for ev in runner.run_async(user_id="test_user", session_id=session.id,
                                     new_message=types.Content(role="user", parts=[types.Part(text=a.ask)])):
        for fc in ev.get_function_calls():
            print(f"              [{ev.author}] tool call: {fc.name} {dict(fc.args)}")
        if ev.is_final_response() and ev.content and ev.content.parts:
            print(f"              [{ev.author}]: {ev.content.parts[0].text.strip()}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="adk 가 내부에서 하는 일을 단계별로 재현")
    p.add_argument("--in_memory", action="store_true", help="adk run --in_memory 와 같은 InMemory 서비스")
    p.add_argument("--session_service_uri", default=None, help="예: sqlite:///tmp_sessions.db, memory://")
    p.add_argument("--ask", default=None, help="질문을 주면 ⑤ 한 턴 실행 (Gemini 키 필요)")
    args = p.parse_args()
    if args.ask:
        from common.bootstrap import require_llm
        require_llm()
    asyncio.run(main(args))
