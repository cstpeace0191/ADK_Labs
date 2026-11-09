"""part09 Graph Workflow 실습 러너.

실행: python run_workflows.py [route|fan|loop|refund|expense|seq|all]
  route · fan · loop · refund · expense : LLM 없이 실행 가능 (refund/expense 는 키가 있으면 LLM 노드 사용)
  seq                                   : Agent 노드 포함 → Gemini 키 필요
"""
import asyncio
import sys

import _path  # noqa: F401
from common.bootstrap import has_llm_credentials
from common.runner_util import Session


async def demo_route():
    from route_workflow.agent import root_agent
    chat = Session(root_agent, app_name="route", verbose=False)
    assert "auto-approved $42" in (await chat.send("42")).final_text
    assert "needs review $250" in (await chat.send("250")).final_text


async def demo_fan():
    from fan_workflow.agent import root_agent
    r = await Session(root_agent, app_name="fan", verbose=False).send("go")
    assert "'a': 'A'" in r.final_text and "'b': 'B'" in r.final_text


async def demo_loop():
    from loop_workflow.agent import root_agent
    r = await Session(root_agent, app_name="loop").send("go")
    assert r.outputs[-1] == "finished after 3 revisions"


async def demo_refund():
    from refund_workflow.agent import root_agent
    await Session(root_agent, app_name="refund", verbose=False).send("ORD-1")  # 자동 승인
    await Session(root_agent, app_name="refund", verbose=False).send("ORD-3")  # 거절
    chat = Session(root_agent, app_name="refund", verbose=False)
    r = await chat.send("ORD-2")                                             # 사람 검토
    assert r.pending, "RequestInput 으로 일시정지되어야 함"
    await chat.resume_input(r.pending, {"approve": True, "note": "VIP 고객 예외 승인"})


async def demo_expense():
    from expense_workflow.agent import root_agent
    await Session(root_agent, app_name="expense", verbose=False).send(
        "from: kim@corp.com amount: 42 category: meal desc: 팀 점심")
    chat = Session(root_agent, app_name="expense", verbose=False)
    r = await chat.send("from: lee@corp.com amount: 780 category: travel desc: 부산 출장 KTX+호텔")
    assert r.pending
    await chat.resume_input(r.pending, "yes")


async def demo_seq():
    if not has_llm_credentials():
        print("(seq: Gemini 키가 없어 건너뜀)")
        return
    from seq_workflow.agent import root_agent
    await Session(root_agent, app_name="seq").send("시작")


DEMOS = {"route": demo_route, "fan": demo_fan, "loop": demo_loop,
         "refund": demo_refund, "expense": demo_expense, "seq": demo_seq}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn in DEMOS.items():
        if which in (name, "all"):
            print(f"\n================ {name} ================")
            asyncio.run(fn())
