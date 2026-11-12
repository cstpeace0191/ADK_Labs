"""강의노트 Part 11 슬라이드 128 '노출': 소수 판별 에이전트를 A2A 서버로.

실행 (part11_eval_deploy/a2a_demo 폴더):
    uvicorn prime_agent.agent:a2a_app --port 8001
에이전트 카드: http://localhost:8001/.well-known/agent-card.json
"""
import os

from google.adk import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a


def check_prime(nums: list[int]) -> dict:
    """주어진 정수들이 소수인지 판별한다."""
    def is_prime(n: int) -> bool:
        return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))
    return {"status": "success", "result": {str(n): is_prime(n) for n in nums}}


root_agent = Agent(
    name="prime_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    description="정수 목록이 소수인지 판별하는 원격 에이전트",
    instruction="숫자가 주어지면 check_prime 으로 판별하고 결과를 간단히 알려라.",
    tools=[check_prime],
)

a2a_app = to_a2a(root_agent, port=8001)
