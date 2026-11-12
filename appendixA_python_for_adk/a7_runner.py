"""부록 A7 ADK Runner (강의노트 _20261111f 슬라이드 195–197, 본문 24–26) — LLM 없이 실행.

실행: python a7_runner.py [run_async|run|parallel|all]
  run_async : async for로 받기 — 호출자가 다음을 요청해야 agent가 진행한다 (196)
  run       : 동기 for로 받기 — 백그라운드 스레드가 앞서 진행, 이벤트는 큐에 쌓인다 (197)
  parallel  : 모델이 도구 2개를 한 번에 요청 → ADK가 동시에 실행 (본문 78 · 부록 180)

run_async · run은 이벤트 3개를 내는 커스텀 에이전트로, parallel은 '대본대로 답하는 모델'로
Runner의 실제 코드를 돌린다. Gemini를 부르지 않는다.
"""
import asyncio
import sys
import time
from typing import AsyncGenerator

import _path  # noqa: F401
from _helpers import Clock, run_turn, scripted_model, section
from common.config import MODEL
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from typing_extensions import override

LABELS = ["E1 function_call", "E2 function_response", "E3 최종 응답"]
SLOW_CONSUMER = 0.2  # 호출자가 이벤트 하나를 처리하는 시간


class Producer(BaseAgent):
    """이벤트를 하나씩 만들 때마다 시각을 찍는 에이전트."""
    log: object = None

    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        for label in LABELS:
            await asyncio.sleep(0.05)  # 모델 · 도구 작업
            self.log(f"agent  : {label} 생성")
            yield Event(author=self.name, invocation_id=ctx.invocation_id,
                        content=types.Content(role="model", parts=[types.Part(text=label)]))


def setup(log):
    ss = InMemorySessionService()
    runner = Runner(agent=Producer(name="producer", log=log), app_name="r", session_service=ss)
    return ss, runner


MSG = types.Content(role="user", parts=[types.Part(text="시작")])


# ---------------------------------------------------------------- run_async (196)
async def demo_run_async() -> None:
    section("run_async: async for로 받기 (슬라이드 196)")
    log = Clock()
    ss, runner = setup(log)
    s = await ss.create_session(app_name="r", user_id="u1")
    async for ev in runner.run_async(user_id="u1", session_id=s.id, new_message=MSG):
        log(f"호출자 : {ev.content.parts[0].text} 받음 → {SLOW_CONSUMER}s 처리")
        await asyncio.sleep(SLOW_CONSUMER)
    print("  → 다음 이벤트는 호출자가 처리를 끝내고 요청한 뒤에 만들어진다 (생산 속도가 호출자에 맞춰짐)")


# ---------------------------------------------------------------- run (197)
def demo_run() -> None:
    section("run: 동기 for로 받기 (슬라이드 197 · 본문 26)")
    log = Clock()
    ss, runner = setup(log)
    s = asyncio.run(ss.create_session(app_name="r", user_id="u1"))
    for ev in runner.run(user_id="u1", session_id=s.id, new_message=MSG):
        log(f"호출자 : {ev.content.parts[0].text} 받음 → {SLOW_CONSUMER}s 처리")
        time.sleep(SLOW_CONSUMER)
    print("  → 백그라운드 스레드가 run_async()를 끝까지 소비해 큐에 쌓고, 호출자는 하나씩 꺼낸다")
    print("    (그래도 '다 모아서 반환'은 아니다: 첫 이벤트는 생기자마자 받는다)")


# ---------------------------------------------------------------- parallel
tool_log = Clock()


async def search_docs(query: str) -> dict:
    """문서를 검색한다."""
    tool_log("search_docs   시작")
    await asyncio.sleep(0.3)
    tool_log("search_docs   끝")
    return {"status": "success", "hits": 2}


async def check_calendar(day: str) -> dict:
    """일정을 확인한다."""
    tool_log("check_calendar 시작")
    await asyncio.sleep(0.3)
    tool_log("check_calendar 끝")
    return {"status": "success", "free": True}


async def demo_parallel() -> None:
    section("parallel: 한 응답에 도구 2개 → 동시에 실행 (본문 78 · 부록 180)")
    agent = LlmAgent(name="assistant", model=MODEL, tools=[search_docs, check_calendar],
                     before_model_callback=scripted_model([
                         [("search_docs", {"query": "ADK"}), ("check_calendar", {"day": "금요일"})],
                         "검색과 일정 확인을 마쳤습니다."]))
    tool_log.t0 = time.perf_counter()
    await run_turn(agent, "ADK 문서 찾고 금요일 일정도 봐 줘")
    print("  → 두 도구가 같은 시각에 시작해 0.3s 뒤 함께 끝난다 (create_task + gather). 순서대로였다면 0.6s")


async def warm_up() -> None:
    """첫 실행의 import 지연이 시간 비교를 흐리지 않도록 한 번 미리 돌린다."""
    ss, runner = setup(lambda _msg: None)
    s = await ss.create_session(app_name="r", user_id="u1")
    async for _ in runner.run_async(user_id="u1", session_id=s.id, new_message=MSG):
        pass


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    asyncio.run(warm_up())
    names = ["run_async", "run", "parallel"] if which == "all" else [which]
    for n in names:
        if n == "run_async":
            asyncio.run(demo_run_async())
        elif n == "run":
            demo_run()
        elif n == "parallel":
            asyncio.run(demo_parallel())
        else:
            sys.exit(f"알 수 없는 항목: {n} (가능: run_async, run, parallel, all)")


if __name__ == "__main__":
    main()
