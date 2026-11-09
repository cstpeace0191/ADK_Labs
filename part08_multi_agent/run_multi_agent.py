"""part08 멀티에이전트 실습 러너 (Gemini 키 필요).

실행: python run_multi_agent.py [help_desk|pipeline|travel|all]
"""
import asyncio
import sys

import _path  # noqa: F401
from common.bootstrap import require_llm
from common.runner_util import Session


async def demo_help_desk():
    from help_desk.agent import root_agent
    chat = Session(root_agent, app_name="help")
    await chat.send("안녕하세요!")                          # 직접 답변
    await chat.send("INV-2026-001 결제가 왜 실패했죠?")       # → billing_agent 로 transfer
    await chat.send("그리고 앱 로그인이 계속 튕겨요")          # → tech_agent


async def demo_pipeline():
    from report_pipeline.agent import root_agent
    chat = Session(root_agent, app_name="report", verbose=False)
    await chat.send("주제: 에이전트 프레임워크의 HITL 기능")
    state = (await chat.get_session()).state
    print("\n최종 draft:\n", state.get("draft"))


async def demo_travel():
    from travel_planner.agent import root_agent
    chat = Session(root_agent, app_name="travel")
    await chat.send("2026-12-05 에 제주 여행 가려고 해. 날씨 확인하고 항공권도 예약해줘")
    await chat.send("창가 좌석으로, 오전 비행기면 좋겠어")  # task 모드 서브에이전트의 질문에 답


DEMOS = {"help_desk": demo_help_desk, "pipeline": demo_pipeline, "travel": demo_travel}

if __name__ == "__main__":
    require_llm()
    which = sys.argv[1] if len(sys.argv) > 1 else "help_desk"
    for name, fn in DEMOS.items():
        if which in (name, "all"):
            print(f"\n================ {name} ================")
            asyncio.run(fn())
