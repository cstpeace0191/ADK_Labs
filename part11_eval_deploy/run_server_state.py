"""강의노트 Part 11 슬라이드 117~118: '서버와 상태'를 누가 책임지나 — LLM 없이 확인한다 (🟢 키 불필요).

실행: python run_server_state.py [lost|shared|factory|all]   (기본 all)
  lost    : 세션 저장소 없이 '인스턴스 A → B'로 요청이 옮겨 가면 대화가 사라진다 (Cloud Run 기본값의 문제)
  shared  : 두 인스턴스가 같은 DB(SessionService)를 보면 대화가 이어진다 (Cloud Run 에서 내가 해야 할 일)
  factory : adk 가 URI·실행 환경을 보고 어떤 SessionService 를 고르는지 (adk web/api_server/deploy 와 같은 코드)

인스턴스 = 서버 프로세스 하나. 여기서는 SessionService 객체 하나가 '컨테이너 하나의 메모리'를 흉내 낸다.
운영 DB 는 Cloud SQL(postgresql+asyncpg://…), 여기서는 같은 SQLAlchemy 경로를 쓰는 SQLite 파일로 대신한다.
"""
import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common.bootstrap  # noqa: E402,F401  (콘솔 UTF-8)

from google.adk.events import Event, EventActions  # noqa: E402
from google.adk.sessions import DatabaseSessionService, InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

APP, USER, SID = "weather_agent", "u1", "s1"


def line(title: str) -> None:
    print(f"\n{'=' * 8} {title} {'=' * 8}")


async def turn_on_instance_a(ss) -> None:
    """인스턴스 A 가 첫 요청을 처리했다고 치고, 대화 이벤트와 State 를 기록한다.

    실제 서버에서는 Runner.run_async() 가 이 일을 한다 (에이전트 코드는 append_event 를 직접 부르지 않는다).
    """
    session = await ss.create_session(app_name=APP, user_id=USER, session_id=SID)
    await ss.append_event(session, Event(
        author="user", invocation_id="inv-1", timestamp=time.time(),
        content=types.Content(role="user", parts=[types.Part(text="내 이름은 민수야. 서울 날씨 알려 줘")]),
        actions=EventActions(state_delta={"user_name": "민수", "last_city": "서울"})))
    print("  [인스턴스 A] 요청 1 처리: 이벤트 1건, State {user_name: 민수, last_city: 서울} 기록")


async def turn_on_instance_b(ss) -> None:
    session = await ss.get_session(app_name=APP, user_id=USER, session_id=SID)
    if session is None:
        print("  [인스턴스 B] 요청 2 '내 이름이 뭐지?' → 세션 s1 없음 → 새 대화로 시작, 이름을 모른다 ✘")
        return
    print(f"  [인스턴스 B] 요청 2 '내 이름이 뭐지?' → 세션 s1 발견: 이벤트 {len(session.events)}건, "
          f"State user_name={session.state.get('user_name')!r} ✔")


async def demo_lost() -> None:
    line("① 세션 저장소 없음: 인스턴스마다 자기 메모리 (InMemorySessionService)")
    await turn_on_instance_a(InMemorySessionService())       # 컨테이너 A 의 메모리
    print("  … 요청이 없어 A 가 0개로 축소되거나, 다음 요청이 다른 인스턴스로 간다 …")
    await turn_on_instance_b(InMemorySessionService())       # 새로 뜬 컨테이너 B 의 메모리 (비어 있음)


async def demo_shared() -> None:
    line("② 바깥 DB 를 같이 본다: DatabaseSessionService (운영=Cloud SQL, 여기=SQLite)")
    with tempfile.TemporaryDirectory() as tmp:
        url = f"sqlite+aiosqlite:///{Path(tmp, 'sessions.db').as_posix()}"
        print(f"  session_service_uri = {url}")
        a = DatabaseSessionService(db_url=url)                # 인스턴스 A
        await turn_on_instance_a(a)
        b = DatabaseSessionService(db_url=url)                # 인스턴스 B (다른 프로세스라고 가정)
        await turn_on_instance_b(b)
        for ss in (a, b):
            await ss.db_engine.dispose()                       # Windows: 파일 잠금 해제 후 임시 폴더 삭제


def demo_factory() -> None:
    line("③ adk 가 고르는 SessionService (create_session_service_from_options)")
    import logging
    logging.getLogger("google_adk").setLevel(logging.ERROR)
    from google.adk.cli.utils.service_factory import create_session_service_from_options

    with tempfile.TemporaryDirectory() as tmp:
        cases = [
            ("로컬 개발 (URI 없음)", None, {}),
            ("Cloud Run (URI 없음)", None, {"K_SERVICE": "weather-agent"}),
            ("URI = memory://", "memory://", {}),
            ("URI = sqlite (DB 파일)", f"sqlite:///{Path(tmp, 's.db').as_posix()}", {}),
            ("URI = agentengine://<id>", "agentengine://1234567890", {}),
        ]
        for label, uri, env in cases:
            saved = {k: os.environ.get(k) for k in env}
            os.environ.update(env)
            try:
                ss = create_session_service_from_options(base_dir=tmp, session_service_uri=uri)
                kind = type(ss).__name__
            except Exception as e:  # noqa: BLE001  (agentengine 은 GCP 프로젝트 설정이 필요할 수 있다)
                kind = f"(생성 실패: {type(e).__name__}) — GCP 프로젝트가 있으면 VertexAiSessionService"
            finally:
                for k, v in saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
            print(f"  {label:<26} → {kind}")
    print("  · Cloud Run 은 K_SERVICE 환경변수로 감지 → 로컬 .adk 대신 메모리 세션 (재시작·축소 때 유실)")
    print("  · 그래서 Cloud Run 배포에는 --session_service_uri 가 필요하다 (deploy/deploy_cloud_run.sh)")
    print("  · agentengine://<id> = 서버는 Cloud Run, 세션만 Agent Runtime 관리형 세션에 맡기는 혼합 구성")
    print("  · Agent Runtime 에 배포하면 GOOGLE_CLOUD_AGENT_ENGINE_ID 가 주입되어 관리형 세션이 자동으로 쓰인다")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("lost", "all"):
        asyncio.run(demo_lost())
    if mode in ("shared", "all"):
        asyncio.run(demo_shared())
    if mode in ("factory", "all"):
        demo_factory()


if __name__ == "__main__":
    main()
