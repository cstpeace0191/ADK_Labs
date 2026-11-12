"""부록 A4 async for · async with (강의노트 _20261111f 슬라이드 186–187) — LLM 없이 실행.

실행: python a4_context_managers.py [aiter|awith|acm|aclosing|runner|all]
  aiter    : __aiter__ / __anext__ / StopAsyncIteration — 페이지를 비동기로 하나씩 (186)
  awith    : __aenter__ / __aexit__ — 예외가 나도 정리된다 (186)
  acm      : @asynccontextmanager — yield 앞은 준비, 뒤는 정리 (187, adk web의 FastAPI lifespan)
  aclosing : 중간에 break한 async generator를 확실히 닫기 (187, Runner 내부)
  runner   : async with Runner(...) — 끝나면 close()가 도구 세트 · 플러그인을 닫는다 (186)
"""
import asyncio
import sys
from contextlib import aclosing, asynccontextmanager

import _path  # noqa: F401
from _helpers import section
from common.config import MODEL
from google.adk.agents import LlmAgent
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.base_toolset import BaseToolset


# ---------------------------------------------------------------- aiter (186)
PAGES = [["doc1", "doc2"], ["doc3"], None]  # 검색 결과 페이지 (None = 끝)


async def fetch_page(i: int):
    await asyncio.sleep(0.02)  # 다음 페이지를 가져오는 I/O
    return PAGES[i]


class Pages:
    def __init__(self):
        self.i = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        page = await fetch_page(self.i)
        self.i += 1
        if page is None:
            raise StopAsyncIteration
        return page


async def demo_aiter() -> None:
    section("aiter: async for = __aiter__ + await __anext__ (슬라이드 186)")
    async for page in Pages():
        print(f"  페이지 받음: {page}")


# ---------------------------------------------------------------- awith (186)
class Connection:
    async def __aenter__(self):
        await asyncio.sleep(0.01)
        print("  __aenter__: 연결 열기")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await asyncio.sleep(0.01)
        print(f"  __aexit__ : 연결 닫기 (예외: {exc_type.__name__ if exc_type else '없음'})")
        return False  # 예외를 삼키지 않는다

    async def query(self, q: str) -> str:
        if q == "bad":
            raise ValueError("잘못된 쿼리")
        return f"{q} 결과"


async def demo_awith() -> None:
    section("awith: 블록에서 예외가 나도 __aexit__는 실행된다 (슬라이드 186)")
    async with Connection() as conn:
        print("  ", await conn.query("ok"))
    try:
        async with Connection() as conn:
            await conn.query("bad")
    except ValueError as e:
        print(f"  바깥에서 예외 확인: {e}")


# ---------------------------------------------------------------- acm (187)
@asynccontextmanager
async def lifespan(app: str):
    print(f"  [{app}] 서비스 시작 (__aenter__ 자리)")
    try:
        yield {"db": "connected"}
    finally:
        print(f"  [{app}] 서비스 종료 (__aexit__ 자리)")


async def demo_acm() -> None:
    section("acm: @asynccontextmanager — 클래스 없이 준비 · 정리 (슬라이드 187)")
    async with lifespan("adk web") as state:
        print(f"  요청 처리 중… state={state}")


# ---------------------------------------------------------------- aclosing (187)
async def events():
    try:
        for i in range(1, 4):
            await asyncio.sleep(0.01)
            yield f"E{i}"
    finally:
        print("    [agen] finally: 남은 작업 정리 (after_run 콜백 · Task 취소 자리)")


async def demo_aclosing() -> None:
    section("aclosing: 중간에 break해도 정리가 바로 실행된다 (슬라이드 187)")
    print("  ① aclosing 없이 break")
    agen = events()
    async for e in agen:
        print(f"    받음 {e} → break")
        break
    print("    블록을 나왔지만 finally는 아직 (가비지 컬렉션 · 루프 종료 때 실행)")
    await agen.aclose()  # 직접 닫아 주어야 한다
    print("  ② aclosing 사용")
    async with aclosing(events()) as agen2:
        async for e in agen2:
            print(f"    받음 {e} → break")
            break
    print("    블록을 나오는 순간 aclose() → finally 이미 실행됨")


# ---------------------------------------------------------------- runner (186)
class DemoToolset(BaseToolset):
    async def get_tools(self, readonly_context=None):
        return []

    async def close(self) -> None:
        print("  DemoToolset.close(): MCP 연결 같은 도구 자원 정리")


class DemoPlugin(BasePlugin):
    async def close(self) -> None:
        print("  DemoPlugin.close(): 플러그인 자원 정리")


async def demo_runner() -> None:
    section("runner: async with Runner(...) as runner (슬라이드 186)")
    agent = LlmAgent(name="assistant", model=MODEL, tools=[DemoToolset()])
    async with Runner(agent=agent, app_name="demo", session_service=InMemorySessionService(),
                      plugins=[DemoPlugin(name="demo_plugin")]) as runner:
        print(f"  블록 안: {type(runner).__name__} 사용 중 (여기서 run_async 등을 호출)")
    print("  블록을 나옴 → Runner.close()가 위의 정리를 호출했다")


DEMOS = {"aiter": demo_aiter, "awith": demo_awith, "acm": demo_acm, "aclosing": demo_aclosing,
         "runner": demo_runner}


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = list(DEMOS) if which == "all" else [which]
    for n in names:
        if n not in DEMOS:
            sys.exit(f"알 수 없는 항목: {n} (가능: {', '.join(DEMOS)}, all)")
        asyncio.run(DEMOS[n]())


if __name__ == "__main__":
    main()
