"""하나의 FastAPI 서버, 두 개의 입구 (agents-cli 생성 서버의 축약판).

  [클라이언트] ──HTTP──> FastAPI ─┬─ /run_sse, /apps/{app}/users/{u}/sessions  (ADK HTTP API, --mode adk)
                                 ├─ /a2a/app/  +  /a2a/app/.well-known/agent-card.json  (A2A, --mode a2a)
                                 └─ /dev-ui/   (web=True 일 때 adk web 과 같은 개발 UI)

원본에는 Agent Runtime 콘솔 플레이그라운드용 /api/reasoning_engine 어댑터도 있다
(vertexai AdkApp 필요 → 실습에서는 생략, README 참고).

실행 (part12_agents_cli 폴더):
    python -m uvicorn app.fast_api_app:app --port 8000
"""
from __future__ import annotations

import contextlib
import os
from collections.abc import AsyncIterator
from pathlib import Path

# .env 는 app/agent.py 맨 앞에서 읽는다 (app 패키지를 import 하는 순간 agent.py 가 먼저 실행되기 때문)
_HERE = Path(__file__).resolve()

from a2a.server.tasks import InMemoryTaskStore  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from google.adk.cli.fast_api import get_fast_api_app  # noqa: E402
from google.adk.runners import Runner  # noqa: E402

from app.app_utils import services  # noqa: E402  (shared:// 등록이 여기서 일어난다)
from app.app_utils.a2a import attach_a2a_routes  # noqa: E402

AGENT_DIR = str(_HERE.parents[1])  # 이 폴더 아래의 "app" 패키지가 /apps/app 으로 노출된다
allow_origins = os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None


@contextlib.asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncIterator[None]:
    from app.agent import app as adk_app
    from app.agent import root_agent

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,  # A2A 요청이 처음 보는 context_id 로 와도 세션을 만든다
    )
    await attach_a2a_routes(fastapi_app, agent=root_agent, runner=runner,
                            task_store=InMemoryTaskStore(), rpc_path=f"/a2a/{adk_app.name}")
    yield


app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,  # /dev-ui (agents-cli playground 가 여는 화면)
    session_service_uri=services.SESSION_SERVICE_URI,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    allow_origins=allow_origins,
    lifespan=lifespan,
)
app.title = "agents-cli-workflow (ADK Labs)"

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "8000")))
