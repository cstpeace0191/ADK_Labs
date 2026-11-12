"""강의노트 Part 4 슬라이드 56: 프로그램에서 실행하기 — Runner + SessionService.

app_name · user_id · session_id 세 축으로 대화를 식별하고,
create_session(state=...)로 초기 State를 주입한다.

실행: python run_with_runner.py [weather|tutor|reviewer|planner|litellm|all]
"""
import asyncio
import sys

import _path  # noqa: F401
from common.bootstrap import require_llm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


async def ask(agent, text: str, state: dict | None = None) -> dict:
    ss = InMemorySessionService()
    runner = Runner(agent=agent, app_name="demo", session_service=ss)
    session = await ss.create_session(app_name="demo", user_id="u1", state=state or {})
    msg = types.Content(role="user", parts=[types.Part(text=text)])
    print(f"\n[{agent.name}] user> {text}")
    async for ev in runner.run_async(user_id="u1", session_id=session.id, new_message=msg):
        for fc in ev.get_function_calls():
            print("   tool:", fc.name, fc.args)
        if ev.content and ev.content.parts:
            for p in ev.content.parts:
                if p.thought and p.text:
                    print("   (thought)", p.text.strip()[:200])
        if ev.is_final_response() and ev.content and ev.content.parts:
            print("   final:", "".join(p.text or "" for p in ev.content.parts if not p.thought).strip())
    s = await ss.get_session(app_name="demo", user_id="u1", session_id=session.id)
    return dict(s.state)


async def main(which: str):
    require_llm()
    if which in ("weather", "all"):
        from weather_agent.agent import root_agent
        await ask(root_agent, "서울 날씨?", state={"course": "Agentic AI"})
        await ask(root_agent, "제주 날씨?", state={"course": "Agentic AI"})
    if which in ("tutor", "all"):
        from tutor_agent.agent import root_agent
        await ask(root_agent, "Runner가 뭐예요?", state={"course": "Agentic AI", "user:name": "김철수"})
    if which in ("reviewer", "all"):
        from reviewer_agent.agent import root_agent
        state = await ask(root_agent, "def div(a, b):\n    return a / b")
        print("   state['review'] =", state.get("review"))
    if which in ("planner", "all"):
        from planner_agent.agent import react_agent, thinking_agent
        await ask(thinking_agent, "17 x 23 은?")
        await ask(react_agent, "주말 서울 1일 여행 계획을 3단계로.")
    if which in ("litellm", "all"):
        from litellm_agent.agent import root_agent
        await ask(root_agent, "안녕?")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "all"))
