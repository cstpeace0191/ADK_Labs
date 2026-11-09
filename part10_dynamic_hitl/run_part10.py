"""part10 Dynamic · HITL · Retry 실습 러너 (모두 LLM 없이 실행된다).

실행: python run_part10.py [dynamic|parallel|hitl|feedback|gate|retry|all]
"""
import asyncio
import logging
import sys

import _path  # noqa: F401
from common.runner_util import Session

logging.getLogger("google_adk").setLevel(logging.ERROR)  # 재시도 traceback 로그 숨김


async def demo_dynamic():
    from dynamic_workflow.agent import root_agent
    r = await Session(root_agent, app_name="dyn", verbose=False).send("go")
    assert r.final_text == "sum of squares=14"


async def demo_parallel():
    from dynamic_parallel.agent import root_agent
    await Session(root_agent, app_name="par", verbose=False).send("ADK, LangGraph, AutoGen")


async def demo_hitl():
    from hitl_workflow.agent import root_agent
    chat = Session(root_agent, app_name="hitl", verbose=False)
    r = await chat.send("시작")
    # ... 프로세스가 종료되고 며칠 뒤 사람이 답해도 세션에 기록이 남아 있으면 재개된다
    await chat.resume_input(r.pending, "21")


async def demo_feedback():
    from feedback_workflow.agent import root_agent
    chat = Session(root_agent, app_name="fb", verbose=False)
    r = await chat.send("서울")
    await chat.resume_input(r.pending, {"liked": ["고궁 산책", "한강 자전거"], "comment": "오전 위주로"})


async def demo_gate():
    from approval_gate.agent import root_agent
    for decision in ({"approve": True, "note": "단골 고객"}, {"approve": False, "note": "정책 위반"}):
        chat = Session(root_agent, app_name="gate", verbose=False)
        r = await chat.send("ORD-777")
        await chat.resume_input(r.pending, decision)
        print("   audit_log:", (await chat.get_session()).state.get("audit_log"))


async def demo_retry():
    from retry_workflow.agent import root_agent
    r = await Session(root_agent, app_name="retry", verbose=False).send("부산")
    assert "3회차 성공" in r.final_text


DEMOS = {"dynamic": demo_dynamic, "parallel": demo_parallel, "hitl": demo_hitl,
         "feedback": demo_feedback, "gate": demo_gate, "retry": demo_retry}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn in DEMOS.items():
        if which in (name, "all"):
            print(f"\n================ {name} ================")
            asyncio.run(fn())
