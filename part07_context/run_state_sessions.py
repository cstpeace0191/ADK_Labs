"""강의노트 Part 7 슬라이드 85~86: State 접두사 + DatabaseSessionService(SQLite) 영속성 (Gemini 키 필요).

- 세션 1에서 이름을 알려주면 user:name 이 저장된다.
- 같은 사용자의 '새' 세션 2에서도 user:name 이 보인다 (세션 범위 visits 는 0부터).
- sessions.db 에 저장되므로 프로그램을 다시 실행해도 user:/app: 값이 남는다.
- 금지 패턴: get_session()으로 가져온 객체를 직접 수정(session.state["x"]=...)하면 영속화되지 않는다.

실행: python run_state_sessions.py
"""
import asyncio
from pathlib import Path

import _path  # noqa: F401
from common.bootstrap import require_llm
from common.runner_util import Session
from google.adk.sessions import DatabaseSessionService
from state_agent.agent import root_agent

DB = Path(__file__).with_name("sessions.db")


async def main():
    require_llm()
    # async with: 끝나면 DB 엔진을 닫는다 (닫지 않으면 aiosqlite 스레드 때문에 프로세스가 종료되지 않는다)
    async with DatabaseSessionService(db_url=f"sqlite+aiosqlite:///{DB.as_posix()}") as ss:
        print("=== 세션 1")
        s1 = Session(root_agent, app_name="state_demo", user_id="u1", session_service=ss,
                     state={"app:notice": "이번 주 금요일 휴강"})
        await s1.send("안녕, 나는 김철수야")
        await s1.send("한 번 더 방문!")
        print("세션1 state:", (await s1.get_session()).state)

        print("\n=== 세션 2 (같은 사용자, 새 대화)")
        s2 = Session(root_agent, app_name="state_demo", user_id="u1", session_service=ss)
        await s2.send("내 이름 기억해?")
        st = (await s2.get_session()).state
        print("세션2 state:", st)
        print("→ user:name 유지:", st.get("user:name"), "/ visits(세션 범위):", st.get("visits"),
              "/ temp:last_tool 저장 안 됨:", "temp:last_tool" not in st)


if __name__ == "__main__":
    asyncio.run(main())
