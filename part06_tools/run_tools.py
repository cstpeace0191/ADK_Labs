"""part06_tools 실습 러너 (Gemini 키 필요).

실행: python run_tools.py [shop|analyst|mcp|openapi|refund|all]   (강의노트 Part 6 슬라이드 70~77)
  shop    : Function Tool + ToolContext state + 결제 전 확인(require_confirmation)
  analyst : AgentTool(google_search 에이전트, 코드실행 에이전트)
  mcp     : MCP 파일시스템 서버 (Node.js 필요)
  openapi : OpenAPI Toolset (먼저 python openapi_agent/hr_mock_server.py)
  refund  : LongRunningFunctionTool — 나중에 승인 결과를 주입
  (Skills/SkillToolset 실습은 Part 5 → ../part05_skills/run_skills.py)
"""
import asyncio
import sys

import _path  # noqa: F401
from common.bootstrap import require_llm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


class Chat:
    def __init__(self, agent):
        self.ss = InMemorySessionService()
        self.runner = Runner(agent=agent, app_name="tools", session_service=self.ss)
        self.sid = None
        self.pending_calls = []  # 장기 실행/확인 대기 function_call

    async def send(self, content: types.Content, label: str):
        if self.sid is None:
            self.sid = (await self.ss.create_session(app_name="tools", user_id="u1")).id
        print(f"\n{label}")
        self.pending_calls = []
        async for ev in self.runner.run_async(user_id="u1", session_id=self.sid, new_message=content):
            long_ids = set(ev.long_running_tool_ids or [])
            for fc in ev.get_function_calls():
                waiting = fc.id in long_ids or fc.name == "adk_request_confirmation"
                print(f"   tool call{' (대기)' if waiting else ''}: {fc.name} {fc.args}")
                if waiting:
                    self.pending_calls.append(fc)
            for fr in ev.get_function_responses():
                print(f"   tool resp: {fr.name} -> {fr.response}")
            if ev.actions and ev.actions.state_delta:
                print("   state_delta:", dict(ev.actions.state_delta))
            if ev.is_final_response() and ev.content and ev.content.parts and ev.content.parts[0].text:
                print("   final:", ev.content.parts[0].text.strip())

    async def say(self, text: str):
        await self.send(types.Content(role="user", parts=[types.Part(text=text)]), f"[user] {text}")

    async def reply_function(self, fc, response: dict):
        part = types.Part(function_response=types.FunctionResponse(id=fc.id, name=fc.name, response=response))
        await self.send(types.Content(role="user", parts=[part]), f"[system → {fc.name}] {response}")


async def demo_shop():
    from shop_agent.agent import root_agent
    chat = Chat(root_agent)
    await chat.say("키보드 1개랑 마우스 2개 담아줘")
    await chat.say("장바구니 보여줘")
    await chat.say("결제해줘")
    for fc in chat.pending_calls:  # adk_request_confirmation
        await chat.reply_function(fc, {"confirmed": True})


async def demo_analyst():
    from analyst_agent.agent import root_agent
    chat = Chat(root_agent)
    await chat.say("Google ADK의 최신 Python 버전을 검색해서 알려줘")
    await chat.say("1부터 100까지 소수의 합을 계산해줘")


async def demo_mcp():
    from mcp_agent.agent import fs_tools, root_agent
    try:
        chat = Chat(root_agent)
        await chat.say("reports 폴더에 어떤 파일이 있고, 3분기 매출 이슈는 뭐야?")
    finally:
        await fs_tools.close()


async def demo_openapi():
    from openapi_agent.agent import root_agent
    chat = Chat(root_agent)
    await chat.say("사번 E1001 연차 몇 일 남았어?")
    await chat.say("올해 남은 회사 공휴일은?")


async def demo_refund():
    from refund_agent.agent import root_agent
    chat = Chat(root_agent)
    await chat.say("주문 ORD-1001 을 35000원 환불해줘")
    # ... 시간이 흐른 뒤 관리자 승인 결과가 외부 시스템에서 도착했다고 가정
    for fc in chat.pending_calls:
        await chat.reply_function(fc, {"status": "approved", "ticket": "TICKET-0001",
                                       "approver": "manager_kim"})


DEMOS = {"shop": demo_shop, "analyst": demo_analyst, "mcp": demo_mcp,
         "openapi": demo_openapi, "refund": demo_refund}

if __name__ == "__main__":
    require_llm()
    which = sys.argv[1] if len(sys.argv) > 1 else "shop"
    for name, fn in DEMOS.items():
        if which in (name, "all"):
            print(f"\n================ {name} ================")
            asyncio.run(fn())
