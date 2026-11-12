"""부록 A3 제너레이터 · 스트리밍 (강의노트 _20261111f 슬라이드 182–185) — LLM 없이 실행.

실행: python a3_generators.py [iter|yield|agen|stream|all]
  iter   : iterator 프로토콜 — 클래스로 직접 vs generator 함수 (182)
  yield  : next() 할 때마다 멈췄다 이어 가는 흐름 (183)
  agen   : generator · 코루틴 · async generator 비교 (184)
  stream : ADK 스트리밍 — partial 이벤트는 바로 yield되지만 세션에는 저장되지 않는다 (185)
           (LLM 대신 토큰 조각을 내는 커스텀 에이전트로 Runner를 실제로 돌린다)
"""
import asyncio
import sys
from typing import AsyncGenerator

import _path  # noqa: F401
from _helpers import Clock, section
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# ---------------------------------------------------------------- iter (182)
class Countdown:
    def __init__(self, n):
        self.n = n

    def __iter__(self):
        return self

    def __next__(self):
        if self.n == 0:
            raise StopIteration
        self.n -= 1
        return self.n + 1


def countdown(n):
    while n > 0:
        yield n  # 값을 내고 멈춤
        n -= 1


def demo_iter() -> None:
    section("iter: for 문이 아는 약속 = iter() + next() + StopIteration (슬라이드 182)")
    print("  클래스 iterator :", list(Countdown(3)))
    print("  generator 함수  :", list(countdown(3)))
    it = iter(countdown(2))
    print("  next(it) →", next(it), "/ next(it) →", next(it))
    try:
        next(it)
    except StopIteration:
        print("  next(it) → StopIteration (for 문은 여기서 끝난다)")


# ---------------------------------------------------------------- yield (183)
def traced(n):
    print("    [gen] 본문 시작")
    while n > 0:
        print(f"    [gen] yield {n} 직전 — 여기서 멈춤")
        yield n
        print(f"    [gen] 재개 (지역 변수 n={n} 그대로)")
        n -= 1
    print("    [gen] 함수 끝 → StopIteration")


def demo_yield() -> None:
    section("yield: 함수를 멈췄다가 이어서 실행 (슬라이드 183)")
    gen = traced(2)
    print("  gen = traced(2) → 본문은 아직 실행 안 됨:", type(gen).__name__)
    for x in gen:
        print(f"  [호출자] {x} 받아서 처리")


# ---------------------------------------------------------------- agen (184)
async def coro_one():
    await asyncio.sleep(0.01)
    return "x"


async def agen_many(n):
    for i in range(n):
        await asyncio.sleep(0.05)  # 기다리면서
        yield f"조각{i + 1}"  # 여러 번 내보낸다


async def demo_agen() -> None:
    section("agen: '멈출 수 있는 함수' 네 가지 (슬라이드 184)")
    print("  일반 함수      :", (lambda: "x")())
    print("  generator      :", list(countdown(2)))
    print("  코루틴         :", await coro_one())
    log = Clock()
    async for piece in agen_many(3):
        log(f"async generator: {piece} — 생기는 즉시 받음")


# ---------------------------------------------------------------- stream (185)
class FakeStreamingModel(BaseAgent):
    """LLM 대신 토큰 조각(partial)을 차례로 내고 마지막에 완성 응답을 내는 에이전트."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        tokens = ["서울은 ", "맑고 ", "기온은 ", "21도입니다."]
        for tok in tokens:
            await asyncio.sleep(0.08)  # 토큰이 생성되는 시간
            yield Event(author=self.name, invocation_id=ctx.invocation_id, partial=True,
                        content=types.Content(role="model", parts=[types.Part(text=tok)]))
        yield Event(author=self.name, invocation_id=ctx.invocation_id,
                    content=types.Content(role="model", parts=[types.Part(text="".join(tokens))]))


async def demo_stream() -> None:
    section("stream: partial 이벤트와 is_final_response() (슬라이드 185)")
    agent = FakeStreamingModel(name="weather_streamer")
    ss = InMemorySessionService()
    runner = Runner(agent=agent, app_name="stream", session_service=ss)
    session = await ss.create_session(app_name="stream", user_id="u1")
    msg = types.Content(role="user", parts=[types.Part(text="서울 날씨?")])
    log = None  # 첫 이벤트 기준 시간 (첫 실행의 import 지연은 빼고 본다)
    screen = ""
    async for event in runner.run_async(user_id="u1", session_id=session.id, new_message=msg):
        log = log or Clock()
        if event.partial:  # 토큰 조각 → 화면에 이어 붙인다
            screen += event.content.parts[0].text
            log(f"partial  → 화면: {screen}")
        elif event.is_final_response():  # 완성된 답
            log(f"최종 응답 → {event.content.parts[0].text}")
    session = await ss.get_session(app_name="stream", user_id="u1", session_id=session.id)
    kinds = ["user" if e.author == "user" else ("partial" if e.partial else "final") for e in session.events]
    print(f"  세션에 저장된 이벤트: {kinds}  → partial 조각은 저장되지 않는다")
    print("  (Gemini에서는 RunConfig(streaming_mode=StreamingMode.SSE)를 줄 때 이런 partial 이벤트가 나온다)")


DEMOS = {"iter": demo_iter, "yield": demo_yield, "agen": demo_agen, "stream": demo_stream}


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = list(DEMOS) if which == "all" else [which]
    for n in names:
        if n not in DEMOS:
            sys.exit(f"알 수 없는 항목: {n} (가능: {', '.join(DEMOS)}, all)")
        r = DEMOS[n]()
        if asyncio.iscoroutine(r):
            asyncio.run(r)


if __name__ == "__main__":
    main()
