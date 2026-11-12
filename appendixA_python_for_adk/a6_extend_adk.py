"""부록 A6 객체 모델 · 확장 (강의노트 _20261111f 슬라이드 191–194) — LLM 없이 실행.

실행: python a6_extend_adk.py [model|custom|callback|decorator|all]
  model     : Agent는 Pydantic 모델 — 이름 규칙 · 오타 인자(extra="forbid") · clone() (191, 본문 51)
  custom    : BaseAgent 상속 + _run_async_impl (async generator)로 커스텀 흐름 (192)
  callback  : 함수를 값으로 — sync · async 콜백 리스트, 플러그인 먼저, 처음 값에서 멈춤 (193, 본문 88–89)
  decorator : functools.wraps 유무에 따른 도구 스키마, ToolContext 주입 (194, 본문 77)
"""
import asyncio
import functools
import json
import sys
import time
from typing import AsyncGenerator

import _path  # noqa: F401
from _helpers import run_turn, scripted_model, section
from common.config import MODEL
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.models import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool, ToolContext
from google.genai import types
from pydantic import ValidationError
from typing_extensions import override


def say(author: str, ctx: InvocationContext, text: str, state: dict | None = None) -> Event:
    return Event(author=author, invocation_id=ctx.invocation_id,
                 content=types.Content(role="model", parts=[types.Part(text=text)]),
                 actions=EventActions(state_delta=state or {}))


# ---------------------------------------------------------------- model (191)
def demo_model() -> None:
    section("model: Agent는 Pydantic 모델이다 (슬라이드 191)")
    for kwargs in ({"name": "my agent"}, {"name": "helper", "instructon": "hi"}, {"name": "user"}):
        try:
            LlmAgent(model=MODEL, **kwargs)
            print(f"  LlmAgent({kwargs}) → 생성됨")
        except ValidationError as e:
            err = e.errors()[0]
            print(f"  LlmAgent({kwargs}) → ValidationError: {err['loc']} {err['msg']}")
    base = LlmAgent(name="helper", model=MODEL, instruction="친절하게 답한다")
    copy = base.clone(update={"name": "helper2"})
    print(f"  clone(update=...) → {copy.name} (instruction 유지: {copy.instruction!r})")


# ---------------------------------------------------------------- custom (192)
class Writer(BaseAgent):
    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        n = ctx.session.state.get("round", 0) + 1
        yield say(self.name, ctx, f"초안 v{n}", {"round": n})


class Critic(BaseAgent):
    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        ok = ctx.session.state.get("round", 0) >= 2
        yield say(self.name, ctx, "승인" if ok else "수정 필요", {"approved": ok})


class ReviewLoop(BaseAgent):
    max_rounds: int = 3

    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        for _ in range(self.max_rounds):
            for agent in self.sub_agents:
                async for event in agent.run_async(ctx):
                    yield event
            if ctx.session.state.get("approved"):
                return


async def demo_custom() -> None:
    section("custom: BaseAgent 상속 + _run_async_impl (슬라이드 192)")
    loop = ReviewLoop(name="review_loop", sub_agents=[Writer(name="writer"), Critic(name="critic")])
    _, _, session = await run_turn(loop, "보고서 써 줘")
    print(f"  최종 state: {dict(session.state)}")
    print("  → 하위 에이전트 이벤트를 async for로 받아 그대로 yield, state를 보고 반복을 멈춘다")


# ---------------------------------------------------------------- callback (193)
calls: list[str] = []
CACHE = {"서울 날씨": "캐시: 맑음 21도"}


class LogPlugin(BasePlugin):
    async def before_model_callback(self, *, callback_context, llm_request):
        calls.append("plugin")
        return None


def log_call(callback_context, llm_request):  # sync 콜백
    calls.append("log_call")
    return None  # 그대로 진행


async def load_cache(callback_context, llm_request):  # async 콜백
    calls.append("load_cache")
    await asyncio.sleep(0.01)  # 캐시 조회 I/O
    question = llm_request.contents[-1].parts[0].text
    hit = CACHE.get(question)
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=hit)])) if hit else None


def stand_in_model(callback_context, llm_request):  # LLM 대신 (실습용)
    calls.append("stand_in_model")
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text="(모델이 답했을 자리)")]))


async def demo_callback() -> None:
    section("callback: 함수를 값으로 넘겨 동작 끼워 넣기 (슬라이드 193)")
    agent = LlmAgent(name="assistant", model=MODEL,
                     before_model_callback=[log_call, load_cache, stand_in_model])
    runner = Runner(agent=agent, app_name="cb", session_service=InMemorySessionService(),
                    plugins=[LogPlugin(name="log_plugin")])
    for q in ("서울 날씨", "부산 날씨"):
        calls.clear()
        await run_turn(agent, q, runner=runner, app_name="cb")
        print(f"    호출 순서: {' → '.join(calls)}")
    print("  → 플러그인 먼저, 리스트는 앞부터, 처음 값을 돌려준 콜백에서 멈춘다 (sync · async 섞어도 됨)")


# ---------------------------------------------------------------- decorator (194)
def timed_ok(func):
    @functools.wraps(func)  # 이름 · docstring · 시그니처 보존
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            print(f"    [timed] {func.__name__}: {time.perf_counter() - start:.3f}s")
    return wrapper


def timed_bad(func):  # wraps 없음
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


async def get_weather(city: str) -> dict:
    """도시의 날씨를 조회한다."""
    await asyncio.sleep(0.02)
    return {"status": "success", "city": city, "temp": 21}


def save_note(text: str, tool_context: ToolContext) -> dict:
    """메모를 세션 상태에 저장한다."""
    tool_context.state["note"] = text
    return {"status": "success"}


def brief(func) -> str:
    d = FunctionTool(func)._get_declaration().model_dump(exclude_none=True)  # noqa: SLF001
    props = (d.get("parameters_json_schema") or {}).get("properties")
    return f"name={d.get('name')!r} description={d.get('description')!r} params={list(props) if props else None}"


async def demo_decorator() -> None:
    section("decorator: 함수를 감싸고 들여다보기 (슬라이드 194)")
    print(f"  wraps 있음: {brief(timed_ok(get_weather))}")
    print(f"  wraps 없음: {brief(timed_bad(get_weather))}")
    print(f"  ToolContext 인자: {brief(save_note)}  ← tool_context는 LLM에게 안 보인다")
    agent = LlmAgent(name="assistant", model=MODEL, tools=[timed_ok(get_weather), save_note],
                     before_model_callback=scripted_model([
                         ("get_weather", {"city": "서울"}),
                         ("save_note", {"text": "서울 21도"}),
                         "메모까지 저장했습니다."]))
    _, _, session = await run_turn(agent, "서울 날씨 보고 메모해 줘")
    print(f"  세션 state: {json.dumps(dict(session.state), ensure_ascii=False)}  ← ADK가 주입한 tool_context로 저장")


DEMOS = {"model": demo_model, "custom": demo_custom, "callback": demo_callback, "decorator": demo_decorator}


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
