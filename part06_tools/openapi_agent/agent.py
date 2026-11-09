"""강의노트 Part 6 슬라이드 76: OpenAPI Toolset과 인증 — 사내 REST API를 도구로.

operationId(get_leave_balance, list_holidays)가 곧 도구 이름이 된다.
API 키는 코드에 하드코딩하지 않고 환경변수(운영: Secret Manager)에서 읽어 헤더로 첨부한다.

먼저 목업 서버 실행: python openapi_agent/hr_mock_server.py
"""
import os
from pathlib import Path

from google.adk import Agent
from google.adk.tools.openapi_tool import OpenAPIToolset

spec = (Path(__file__).parent / "hr_api.yaml").read_text(encoding="utf-8")

hr_tools = OpenAPIToolset(
    spec_str=spec,
    spec_str_type="yaml",
    header_provider=lambda ctx: {"X-API-Key": os.getenv("HR_API_KEY", "demo-hr-key")},
)

root_agent = Agent(
    name="hr_bot",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    tools=[hr_tools],
    instruction="휴가 잔여일은 HR API(get_leave_balance)로만 조회하라. 공휴일은 list_holidays.",
)
