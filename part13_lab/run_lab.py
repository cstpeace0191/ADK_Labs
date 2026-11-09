"""part13_lab 종합 실습: 학사 문의 에이전트를 단계별로 키우기.

실행: python run_lab.py [1|2|3|4|5|all]
  1·2·3단계 : LlmAgent → Gemini 키 필요 (3단계의 개인정보 차단은 키 없이도 동작)
  4·5단계   : Workflow → 키 없이 실행 (일반 문의 노드만 키가 있으면 LLM 사용)
로그인 정보는 세션 초기 State 로 주입한다: user:student_id, user:name
"""
import asyncio
import logging
import sys

import _path  # noqa: F401
from common.bootstrap import has_llm_credentials
from common.runner_util import Session

logging.getLogger("google_adk").setLevel(logging.ERROR)
LOGIN = {"user:student_id": "S001", "user:name": "김철수"}


async def step1():
    from step1_basic.agent import root_agent
    await Session(root_agent, app_name="lab").send("수강신청 정정 기간이 언제예요?")


async def step2():
    from step2_tools.agent import root_agent
    chat = Session(root_agent, app_name="lab", state=LOGIN)
    await chat.send("이번 학기 내 수강 과목이랑 총 학점 알려줘")
    await chat.send("선형대수 성적은?")
    print("   state.last_courses =", (await chat.get_session()).state.get("last_courses"))


async def step3():
    from step3_callback.agent import root_agent
    chat = Session(root_agent, app_name="lab", state=LOGIN)
    r = await chat.send("제 학번은 20261234이고 비밀번호: abc123 인데 성적 알려주세요")
    assert "개인정보" in r.final_text
    if has_llm_credentials():
        await chat.send("CS1O1 성적 알려줘")  # 오타(O) → before_tool_callback 형식 검증


async def step4():
    from step4_workflow.agent import root_agent
    for q in ["내 성적 전부 보여줘", "CS101 성적은?", "이번 학기 수강 과목 알려줘",
              "주민번호 900101-1234567 로 조회해줘", "도서관 운영 시간은?"]:
        await Session(root_agent, app_name="lab", state=LOGIN, verbose=False).send(q)


async def step5():
    from step5_hitl_retry.agent import root_agent
    chat = Session(root_agent, app_name="lab", state=LOGIN, verbose=False)
    r = await chat.send("MA110 수강 취소하고 싶어요")  # 외부 API 재시도 → 승인 요청에서 멈춤
    assert r.pending
    await chat.resume_input(r.pending, {"confirm": True, "reason": "학점 과다"})
    await chat.send("이번 학기 수강 과목 알려줘")
    chat2 = Session(root_agent, app_name="lab", state=LOGIN, verbose=False)
    r = await chat2.send("AI201 수강취소")
    await chat2.resume_input(r.pending, {"confirm": False, "reason": "다시 생각해봄"})


STEPS = {"1": step1, "2": step2, "3": step3, "4": step4, "5": step5}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for k, fn in STEPS.items():
        if which in (k, "all"):
            print(f"\n================ step {k} ================")
            if k in ("1", "2") and not has_llm_credentials():
                print("(Gemini 키가 없어 건너뜀)")
                continue
            asyncio.run(fn())
