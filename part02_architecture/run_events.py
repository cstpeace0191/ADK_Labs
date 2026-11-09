"""part02: 요청 한 번의 생명주기를 Event로 관찰한다 (Gemini 키 필요).

강의노트 Part 2 슬라이드 21~24: 사용자 → Runner → Agent ↔ Gemini ↔ Tools, 모든 것은 Event로 기록된다.
실행: uv run run_events.py
"""
import asyncio
import importlib

import _path  # noqa: F401
from common.bootstrap import require_llm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from chat_time_weather_agent.agent import root_agent


async def run_query(runner: Runner, session_id: str, prompt: str):
    print(f"\n================ [User Message] {prompt} ================")
    msg = types.Content(role="user", parts=[types.Part(text=prompt)])

    async for event in runner.run_async(user_id="u1", session_id=session_id, new_message=msg):
        print(f"--- Event author={event.author}")
        if event.get_function_calls():
            for fc in event.get_function_calls():
                print(f"  ① 모델이 도구 호출 요청: {fc.name}({fc.args})")
        if event.get_function_responses():
            for fr in event.get_function_responses():
                print(f"  ② Runner가 도구를 실행한 결과: {fr.response}")
        if event.actions and event.actions.state_delta:
            print("  state_delta:", dict(event.actions.state_delta))
        if event.is_final_response():
            print("  ③ 최종 응답:\n", event.content.parts[0].text)


async def main():
    require_llm()
    ss = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name="demo", session_service=ss)
    session = await ss.create_session(app_name="demo", user_id="u1")

    # 1. 시간 및 날씨 질문 (도구 호출 Event 관찰)
    await run_query(runner, session.id, "서울의 현재 시간과 날씨 알려줘")

    # 2. 일반 질문 (도구 호출 없이 직접 응답하는 Event 관찰)
    await run_query(runner, session.id, "안녕! 너는 어떤 일을 도와줄 수 있니?")

    s = await ss.get_session(app_name="demo", user_id="u1", session_id=session.id)
    print(f"\n세션에 기록된 총 이벤트 수: {len(s.events)}")


if __name__ == "__main__":
    asyncio.run(main())
