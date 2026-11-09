"""Runner 실행 도우미 (강의노트 Part 4 '프로그램에서 실행하기' 패턴을 재사용).

- run_turn(): 사용자 메시지 1턴을 실행하고 이벤트를 출력
- resume_input(): RequestInput(HITL)으로 멈춘 워크플로우에 사람 응답을 보내 재개
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

REQUEST_INPUT = "adk_request_input"


@dataclass
class TurnResult:
    final_text: str | None = None
    outputs: list[Any] = field(default_factory=list)
    # (interrupt_id, invocation_id) — RequestInput으로 일시정지된 경우
    pending: tuple[str, str] | None = None


def _print_event(ev, verbose: bool, result: TurnResult) -> None:
    if ev.content and ev.content.parts:
        for p in ev.content.parts:
            if p.function_call:
                if p.function_call.name == REQUEST_INPUT:
                    args = p.function_call.args or {}
                    print(f"  [HITL] {args.get('message')}")
                    if args.get("payload") is not None:
                        print(f"         payload={args.get('payload')}")
                    result.pending = (p.function_call.id, ev.invocation_id)
                elif verbose:
                    print(f"  [tool call] {p.function_call.name}({json.dumps(p.function_call.args, ensure_ascii=False)})")
            elif p.function_response and verbose:
                print(f"  [tool resp] {p.function_response.name} -> {p.function_response.response}")
            elif p.text and not getattr(p, "thought", False):
                print(f"  [{ev.author}] {p.text.strip()}")
                if ev.is_final_response():
                    result.final_text = p.text
    out = getattr(ev, "output", None)
    if out is not None:
        result.outputs.append(out)
        if verbose:
            # node_info.path 예: "loop_workflow@1/critic@2" → 마지막 조각(노드명@실행회차)만 표시
            path = getattr(getattr(ev, "node_info", None), "path", None) or ev.author
            print(f"  [output:{path.rsplit('/', 1)[-1]}] {out}")
    if verbose and ev.actions and ev.actions.state_delta:
        print(f"  [state_delta] {dict(ev.actions.state_delta)}")


class Session:
    """app_name · user_id · session_id 세 축으로 대화를 묶는 작은 래퍼."""

    def __init__(self, agent, app_name: str = "demo", user_id: str = "u1",
                 state: dict | None = None, session_service=None,
                 memory_service=None, plugins=None, verbose: bool = True):
        self.app_name, self.user_id, self.verbose = app_name, user_id, verbose
        self.initial_state = state or {}
        self.session_service = session_service or InMemorySessionService()
        self.runner = Runner(agent=agent, app_name=app_name,
                             session_service=self.session_service,
                             memory_service=memory_service, plugins=plugins)
        self.session_id: str | None = None

    async def _ensure(self):
        if self.session_id is None:
            s = await self.session_service.create_session(
                app_name=self.app_name, user_id=self.user_id, state=self.initial_state)
            self.session_id = s.id

    async def _run(self, msg: types.Content, invocation_id: str | None = None) -> TurnResult:
        await self._ensure()
        result = TurnResult()
        async for ev in self.runner.run_async(user_id=self.user_id, session_id=self.session_id,
                                              new_message=msg, invocation_id=invocation_id):
            _print_event(ev, self.verbose, result)
        return result

    async def send(self, text: str) -> TurnResult:
        print(f"\n[user] {text}")
        return await self._run(types.Content(role="user", parts=[types.Part(text=text)]))

    async def resume_input(self, pending: tuple[str, str], response: Any) -> TurnResult:
        """RequestInput에 대한 사람 응답. dict가 아니면 {'result': value}로 감싼다."""
        interrupt_id, invocation_id = pending
        print(f"\n[human] {response}")
        payload = response if isinstance(response, dict) else {"result": response}
        part = types.Part(function_response=types.FunctionResponse(
            id=interrupt_id, name=REQUEST_INPUT, response=payload))
        return await self._run(types.Content(role="user", parts=[part]), invocation_id)

    async def get_session(self):
        await self._ensure()
        return await self.session_service.get_session(
            app_name=self.app_name, user_id=self.user_id, session_id=self.session_id)
