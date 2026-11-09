"""강의노트 Part 3 슬라이드 27~29 · 33: 직접 Runner 코드 — 등록 → 실행 → 이벤트 소비 (Gemini 키 필요).

adk CLI 없이, 응용 SW가 Runner 를 직접 만들어 agent loop 를 돌린다.
같은 my_agent/agent.py 를 `adk run my_agent` 로도 실행할 수 있다 (adk 가 아래 ①을 대신 해 준다).

실행 (part03_cli 폴더): python run_direct_runner.py ["질문"]
"""
import asyncio
import sys

import _path  # noqa: F401  (실습 루트 .env + 재시도 설정)
from common.bootstrap import require_llm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from my_agent.agent import root_agent  # 에이전트 정의 (agent.py 의 root_agent)


async def main(question: str) -> None:
    require_llm()

    # ① 등록: root_agent 와 서비스로 Runner 객체를 만든다
    ss = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name="demo", session_service=ss)
    session = await ss.create_session(app_name="demo", user_id="u1")
    print(f"① 등록   Runner(agent={root_agent.name}, session_service=InMemorySessionService)")
    print(f"         세션 생성 app_name=demo · user_id=u1 · session_id={session.id[:8]}…")

    # ② 실행: run_async() 한 번 = agent loop 한 바퀴 (슬라이드 29의 1~5단계)
    msg = types.Content(role="user", parts=[types.Part(text=question)])
    print(f"② 실행   run_async(new_message={question!r})")
    step = 0
    async for ev in runner.run_async(user_id="u1", session_id=session.id, new_message=msg):
        step += 1
        # ③ 소비: 응용 SW 가 이벤트를 골라 쓴다
        for fc in ev.get_function_calls():
            print(f"   [Event {step}] 모델 호출 → function_call {fc.name}({dict(fc.args)})   (모델은 요청만)")
        for fr in ev.get_function_responses():
            print(f"   [Event {step}] 도구 실행 → function_response {fr.name}: {fr.response}   (Runner 가 실행)")
        if ev.actions and ev.actions.state_delta:
            print(f"   [Event {step}] state_delta {dict(ev.actions.state_delta)}")
        if ev.is_final_response() and ev.content and ev.content.parts:
            print(f"③ 소비   최종 응답(Event {step}): {ev.content.parts[0].text.strip()}")

    s = await ss.get_session(app_name="demo", user_id="u1", session_id=session.id)
    print(f"         세션에 기록된 이벤트 {len(s.events)}개 (사용자 메시지 · 도구 호출 · 결과 · 응답)")
    print("\n나머지(입력 루프 · 세션 저장소 선택 · HTTP 서버)는 응용 SW 몫 → adk CLI 는 이것을 대신 해 준다 (adk_internals.py)")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "서울 날씨 알려줘"))
