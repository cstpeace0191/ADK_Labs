"""모든 서빙 입구(ADK HTTP API, A2A)가 같은 Session·Artifact 서비스를 쓰게 한다.

agents-cli 생성 코드의 핵심 아이디어: "shared://" URI 스킴을 서비스 레지스트리에 등록해
get_fast_api_app(session_service_uri="shared://session") 과 A2A 용 Runner 가 **같은 인스턴스**를 받는다.
그래서 /run_sse 로 만든 세션을 A2A 쪽에서도 볼 수 있다.

우선순위 (원본과 동일):
  1) SESSION_SERVICE_URI 환경변수 (예: sqlite:///sessions.db, postgresql://...)
  2) GOOGLE_CLOUD_AGENT_ENGINE_ID 가 있으면 VertexAiSessionService (Agent Runtime 에 배포된 경우)
  3) 그 외 InMemorySessionService (개발용)
"""
from __future__ import annotations

import functools
import os

from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.adk.cli.service_registry import get_service_registry
from google.adk.cli.utils.service_factory import create_session_service_from_options

SESSION_SERVICE_URI = "shared://session"
ARTIFACT_SERVICE_URI = "shared://artifact"

_AGENT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@functools.cache
def get_session_service():
    """프로세스 전체에서 하나만 쓰는 세션 서비스."""
    if uri := os.environ.get("SESSION_SERVICE_URI"):
        return create_session_service_from_options(base_dir=_AGENT_DIR, session_service_uri=uri)
    if engine_id := os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID"):
        from google.adk.sessions.vertex_ai_session_service import VertexAiSessionService

        return VertexAiSessionService(
            project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            location=os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_LOCATION")
            or os.environ.get("GOOGLE_CLOUD_LOCATION"),
            agent_engine_id=engine_id,
        )
    from google.adk.sessions import InMemorySessionService

    return InMemorySessionService()


@functools.cache
def get_artifact_service():
    """LOGS_BUCKET_NAME 이 있으면 GCS, 없으면 메모리."""
    if bucket := os.environ.get("LOGS_BUCKET_NAME"):
        return GcsArtifactService(bucket_name=bucket)
    return InMemoryArtifactService()


_registry = get_service_registry()
_registry.register_session_service("shared", lambda uri, **kw: get_session_service())
_registry.register_artifact_service("shared", lambda uri, **kw: get_artifact_service())
