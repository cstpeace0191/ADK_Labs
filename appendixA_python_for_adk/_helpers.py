"""부록 A 실습 공통 도우미 (모두 LLM 없이 동작).

- section(): 실습 단계 제목 출력
- Clock: 실행 시작부터 지난 시간을 붙여 출력
- scripted_model(): before_model_callback으로 '대본대로 답하는 모델'을 만든다.
  LLM을 부르지 않고도 Runner의 실제 도구 호출 루프(function_call → 도구 실행 →
  function_response → 모델 재호출)를 그대로 돌려 볼 수 있다. (부록 A6 콜백 슬라이드의 원리)
- run_turn(): Runner로 한 턴을 실행하고 이벤트를 요약 출력
"""
from __future__ import annotations

import json
import time
from typing import Any, Callable

from google.adk.models import LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def section(title: str) -> None:
    print(f"\n=== {title} ===")


class Clock:
    def __init__(self) -> None:
        self.t0 = time.perf_counter()

    def __call__(self, msg: str) -> None:
        print(f"  {time.perf_counter() - self.t0:5.2f}s  {msg}")


def _text(t: str) -> LlmResponse:
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=t)]))


def _calls(calls: list[tuple[str, dict]]) -> LlmResponse:
    parts = [types.Part(function_call=types.FunctionCall(name=n, args=a)) for n, a in calls]
    return LlmResponse(content=types.Content(role="model", parts=parts))


def scripted_model(script: list[Any]) -> Callable:
    """모델 호출 순서대로 응답을 돌려주는 before_model_callback을 만든다.

    script 원소: str → 텍스트 응답, (name, args) → 도구 호출 1개,
                [(name, args), ...] → 한 응답에 도구 호출 여러 개(병렬 호출)
    """
    steps = list(script)

    def before_model(callback_context, llm_request):
        if not steps:
            return _text("(대본 끝)")
        step = steps.pop(0)
        if isinstance(step, str):
            return _text(step)
        if isinstance(step, tuple):
            return _calls([step])
        return _calls(step)

    return before_model


async def run_turn(agent, text: str, *, app_name: str = "appendix_a", state: dict | None = None,
                   show: bool = True, runner: Runner | None = None, session_service=None):
    """한 턴 실행. (최종 텍스트, 이벤트 목록, 세션)을 돌려준다."""
    ss = session_service or InMemorySessionService()
    runner = runner or Runner(agent=agent, app_name=app_name, session_service=ss)
    ss = runner.session_service
    session = await ss.create_session(app_name=app_name, user_id="u1", state=state or {})
    msg = types.Content(role="user", parts=[types.Part(text=text)])
    events, final = [], None
    if show:
        print(f"  [user] {text}")
    async for ev in runner.run_async(user_id="u1", session_id=session.id, new_message=msg):
        events.append(ev)
        if not show or not (ev.content and ev.content.parts):
            continue
        for p in ev.content.parts:
            if p.function_call:
                print(f"  [{ev.author}] function_call {p.function_call.name}({json.dumps(p.function_call.args, ensure_ascii=False)})")
            elif p.function_response:
                print(f"  [{ev.author}] function_response {p.function_response.name} -> {p.function_response.response}")
            elif p.text:
                print(f"  [{ev.author}] {p.text.strip()}")
                if ev.is_final_response():
                    final = p.text
    session = await ss.get_session(app_name=app_name, user_id="u1", session_id=session.id)
    return final, events, session
