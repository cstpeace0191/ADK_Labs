"""part05_skills 실습 러너 (Gemini 키 필요) — 강의노트 Part 5 슬라이드 63~67.

실행: python run_skills.py [weather|greeting|all]   (기본 all)
  weather  : 발견(list_skills) → 활성화(load_skill) → get_weather(adk_additional_tools) →
             실행(run_skill_script: scripts/outdoor_rule.py) → load_skill_resource(references · assets)
  greeting : 코드로 정의한 스킬(models.Skill)의 references/hello.txt 를 읽어 인사
LLM 없이 구조만 보려면: python skills_explorer.py
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
        self.runner = Runner(agent=agent, app_name="skills", session_service=self.ss)
        self.sid = None

    async def say(self, text: str):
        if self.sid is None:
            self.sid = (await self.ss.create_session(app_name="skills", user_id="u1")).id
        print(f"\n[user] {text}")
        msg = types.Content(role="user", parts=[types.Part(text=text)])
        async for ev in self.runner.run_async(user_id="u1", session_id=self.sid, new_message=msg):
            for fc in ev.get_function_calls():
                print(f"   tool call: {fc.name} {fc.args}")
            for fr in ev.get_function_responses():
                print(f"   tool resp: {fr.name} -> {str(fr.response)[:160]}")
            if ev.actions and ev.actions.state_delta:
                print("   state_delta:", dict(ev.actions.state_delta))
            if ev.is_final_response() and ev.content and ev.content.parts and ev.content.parts[0].text:
                print("   final:", ev.content.parts[0].text.strip())


async def demo_weather():
    from skills_agent.agent import root_agent
    await Chat(root_agent).say("서울, 제주, 대구, 광주 날씨 브리핑 써줘. 야외 활동 가능해?")


async def demo_greeting():
    from skills_agent.agent import root_agent
    await Chat(root_agent).say("김민수 학생에게 환영 인사 해줘")


DEMOS = {"weather": demo_weather, "greeting": demo_greeting}

if __name__ == "__main__":
    require_llm()
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn in DEMOS.items():
        if which in (name, "all"):
            print(f"\n================ {name} ================")
            asyncio.run(fn())
