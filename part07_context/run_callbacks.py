"""강의노트 Part 7 슬라이드 88~89: Callback 가드레일 + AuditPlugin.

1) 금칙어 입력 → before_model_callback 이 LLM 호출 없이 차단 (키 없이도 동작)
2) qty>10 → before_tool_callback 이 도구 실행을 막고 오류 dict 반환 (Gemini 키 필요)
3) 정상 요청 → AuditPlugin 이 도구 실행 시간을 기록 (Gemini 키 필요)

실행: python run_callbacks.py
"""
import asyncio

import _path  # noqa: F401
from audit_plugin import AuditPlugin
from common.bootstrap import has_llm_credentials
from common.runner_util import Session
from guarded_agent.agent import root_agent


async def main():
    audit = AuditPlugin()
    chat = Session(root_agent, app_name="guard", plugins=[audit])

    r = await chat.send("내 주민등록번호는 900101-1234567 이야")
    assert r.final_text == "민감정보는 처리할 수 없습니다."
    print("   → state.blocked_count =", (await chat.get_session()).state.get("blocked_count"))

    if not has_llm_credentials():
        print("\n(Gemini 키가 없어 2)·3) 단계는 건너뜀)")
        return
    await chat.send("SKU-123 을 20개 담아줘")
    await chat.send("SKU-123 을 2개 담아줘")
    print("\n감사 로그:", audit.log)


if __name__ == "__main__":
    asyncio.run(main())
