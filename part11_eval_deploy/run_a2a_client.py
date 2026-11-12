"""강의노트 Part 11 슬라이드 128: A2A 소비 측 실행 (Gemini 키 필요).

터미널 A (a2a_demo 폴더):  uvicorn prime_agent.agent:a2a_app --port 8001
터미널 B (part11_eval_deploy): python run_a2a_client.py
"""
import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE / "a2a_demo")]
import common.bootstrap  # noqa: E402,F401
from common.bootstrap import require_llm  # noqa: E402
from common.runner_util import Session  # noqa: E402


async def main():
    require_llm()
    import httpx
    try:
        httpx.get("http://localhost:8001/.well-known/agent-card.json", timeout=3).raise_for_status()
    except Exception:
        print("prime_agent A2A 서버가 없습니다. a2a_demo 폴더에서: uvicorn prime_agent.agent:a2a_app --port 8001")
        return
    from host_agent.agent import root_agent
    chat = Session(root_agent, app_name="a2a_host")
    await chat.send("주사위 3개 굴리고, 나온 숫자들이 소수인지 확인해줘")


if __name__ == "__main__":
    asyncio.run(main())
