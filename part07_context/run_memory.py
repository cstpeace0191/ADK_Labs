"""강의노트 Part 7 슬라이드 82: 세션 종료 → add_session_to_memory → 다음 세션에서 preload/load (Gemini 키 필요).

운영에서는 InMemoryMemoryService 대신 VertexAiMemoryBankService(사실 자동 추출·병합)를 쓴다.
실행: python run_memory.py
"""
import asyncio

import _path  # noqa: F401
from common.bootstrap import require_llm
from common.runner_util import Session
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from memory_agent.agent import root_agent


async def main():
    require_llm()
    ss = InMemorySessionService()
    memory = InMemoryMemoryService()

    print("=== 세션 1: 사실을 알려준다")
    s1 = Session(root_agent, app_name="mem", user_id="u1", session_service=ss, memory_service=memory)
    await s1.send("나는 매운 음식을 못 먹고, 다음 주 화요일에 부산 출장이 있어.")
    # 세션이 끝나면 장기 기억으로 옮긴다
    await memory.add_session_to_memory(await s1.get_session())
    print("→ 세션 1을 Memory에 저장")

    print("\n=== 세션 2: 새 대화 (State는 비어 있음)")
    s2 = Session(root_agent, app_name="mem", user_id="u1", session_service=ss, memory_service=memory)
    await s2.send("출장지에서 저녁 메뉴 추천해줘")


if __name__ == "__main__":
    asyncio.run(main())
