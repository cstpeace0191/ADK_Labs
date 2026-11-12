"""강의노트 Part 10 슬라이드 112: RetryConfig 와 timeout — 노드 단위 내구성 (LLM 없음).

fetch_forecast 는 처음 2번 ConnectionError, 3번째 시도에 성공한다 (max_attempts=3).
시도마다 timeout 을 넘기면 NodeTimeoutError 가 나고, exceptions 에 포함되어 있으므로 역시 재시도된다.
(실행 중 출력되는 ConnectionError traceback 은 재시도 로그로, 정상 동작이다.)
재시도는 노드 전체를 다시 실행하므로 쓰기 작업은 멱등하게 만들거나 성공 이후 노드로 옮긴다.
"""
import asyncio

from google.adk import Event, Workflow
from google.adk.workflow import NodeTimeoutError, RetryConfig, node

_attempts = {"forecast": 0}


async def weather_api(city: str) -> str:
    _attempts["forecast"] += 1
    if _attempts["forecast"] < 3:
        raise ConnectionError(f"일시적 네트워크 오류 (시도 {_attempts['forecast']})")
    return f"{city}: 맑음 18°C (시도 {_attempts['forecast']}회차 성공)"


@node(
    retry_config=RetryConfig(
        max_attempts=3,       # 원 실행 포함 → 재시도 2회
        initial_delay=0.2,    # 이후 x2 백오프 (기본 1.0초, 최대 60초)
        jitter=0,             # 테스트는 0
        exceptions=[ConnectionError, NodeTimeoutError],
    ),
    timeout=10.0,             # 시도마다 10초
)
async def fetch_forecast(node_input: str):
    return await weather_api(node_input.strip() or "서울")


def report(node_input: str):
    return Event(message=f"예보: {node_input}")


root_agent = Workflow(name="retry_workflow", edges=[("START", fetch_forecast, report)])
