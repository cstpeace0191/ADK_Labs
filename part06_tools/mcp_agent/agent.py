"""강의노트 Part 6 슬라이드 80: MCP Toolset — 표준 프로토콜로 외부 도구(파일시스템 서버) 연결.

필요: Node.js(npx), `pip install "mcp>=1.24,<2"`  (mcp 2.x 는 현재 ADK와 호환되지 않음)
tool_filter 로 읽기 도구만 노출(최소 권한).
"""
import os
from pathlib import Path

from google.adk import Agent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

REPORTS_DIR = str((Path(__file__).resolve().parents[1] / "data" / "reports"))

fs_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx.cmd" if os.name == "nt" else "npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", REPORTS_DIR],
        ),
        timeout=30,
    ),
    tool_filter=["read_text_file", "read_file", "list_directory"],  # 최소 권한
)

root_agent = Agent(
    name="file_assistant",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    instruction=f"{REPORTS_DIR} 폴더의 파일만 읽어 답하라. 먼저 list_directory로 목록을 확인한다.",
    tools=[fs_tools],
)
