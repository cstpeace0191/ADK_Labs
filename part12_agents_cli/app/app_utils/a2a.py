"""같은 FastAPI 앱에 A2A(JSON-RPC + Agent Card) 라우트를 붙인다.

agents-cli 원본(app_utils/a2a.py)은 a2a-sdk 1.x 의 create_jsonrpc_routes 를 직접 쓴다.
실습 환경(google-adk 2.6 + a2a-sdk 0.3)에서도 돌도록, ADK 가 a2a-sdk 0.3/1.x 차이를 흡수하려고
만든 내부 헬퍼(google.adk.a2a._compat.attach_a2a_routes_to_app)를 쓴다. 하는 일은 같다:

  GET  {rpc_path}/.well-known/agent-card.json   ← 에이전트 명함(이름·설명·스킬·호출 URL)
  POST {rpc_path}                               ← A2A JSON-RPC (message/send, message/stream)
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from google.adk.a2a import _compat  # 내부 API: ADK 버전이 바뀌면 확인 필요
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder

if TYPE_CHECKING:
    from fastapi import FastAPI
    from google.adk.agents import BaseAgent
    from google.adk.runners import Runner


def resolve_app_url(app_url: str | None = None) -> str:
    """Agent Card 에 적을 공개 주소. 명시값 → APP_URL → Agent Runtime 주소 → 로컬 기본값 순."""
    if app_url:
        return app_url
    if env_url := os.getenv("APP_URL"):
        return env_url
    engine_id = os.getenv("GOOGLE_CLOUD_AGENT_ENGINE_ID")
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_AGENT_ENGINE_LOCATION", "us-east1")
    if engine_id and project:
        # Agent Runtime 은 /api 아래로 컨테이너의 HTTP 경로를 그대로 통과시킨다
        return (f"https://{location}-aiplatform.googleapis.com/reasoningEngines/v1"
                f"/projects/{project}/locations/{location}/reasoningEngines/{engine_id}/api")
    return "http://127.0.0.1:8000"


async def attach_a2a_routes(app: FastAPI, *, agent: BaseAgent, runner: Runner,
                            task_store, rpc_path: str, app_url: str | None = None) -> None:
    """Agent Card 를 만들고 A2A 라우트를 app 에 등록한다. FastAPI lifespan 에서 한 번 호출한다."""
    card = await AgentCardBuilder(
        agent=agent,
        rpc_url=f"{resolve_app_url(app_url)}{rpc_path}/",
    ).build()
    _compat.attach_a2a_routes_to_app(
        app,
        agent_card=card,
        # Runner 를 공유하므로 A2A 로 들어온 대화도 같은 세션 서비스에 저장된다
        agent_executor=A2aAgentExecutor(runner=runner),
        task_store=task_store,
        prefix=rpc_path,
    )
