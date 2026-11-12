"""강의노트 Part 11 슬라이드 128 '소비': 원격 A2A 에이전트를 하위 에이전트로 사용.

먼저 prime_agent A2A 서버를 띄운 뒤 (uvicorn prime_agent.agent:a2a_app --port 8001)
    adk web          (a2a_demo 폴더에서 → host_agent 선택)
또는
    python ../run_a2a_client.py
"""
import os

from google.adk import Agent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent

PRIME_URL = os.getenv("PRIME_AGENT_URL", "http://localhost:8001")

prime = RemoteA2aAgent(
    name="prime_agent",
    description="정수 목록이 소수인지 판별하는 원격 에이전트",
    agent_card=f"{PRIME_URL}{AGENT_CARD_WELL_KNOWN_PATH}",
)


def roll_dice(sides: int = 6, count: int = 3) -> dict:
    """주사위를 굴린다."""
    import random
    return {"status": "success", "rolls": [random.randint(1, sides) for _ in range(count)]}


root_agent = Agent(
    name="host_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    instruction="주사위는 roll_dice 로 직접 굴린다. 소수 판별은 prime_agent 에게 넘긴다.",
    tools=[roll_dice],
    sub_agents=[prime],
)
