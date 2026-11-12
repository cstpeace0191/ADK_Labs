"""ADK Docs MCP 서버(mcpdoc)를 직접 띄워 코딩 에이전트가 받는 도구를 확인한다.

코딩 에이전트(Claude Code · Antigravity · Cursor)가 하는 일과 같다:
  1) `uvx --from mcpdoc --with "mcp<2" mcpdoc --urls AgentDevelopmentKit:https://adk.dev/llms.txt --transport stdio` 실행
  2) MCP initialize → tools/list → tools/call

실행 (mcp 1.x 클라이언트가 필요해서 uv 로 임시 환경을 만든다):
  uv run --no-project --with "mcp<2" python check_mcpdoc.py
"""
import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 공식 문서(adk.dev/tutorials/coding-with-ai)의 설정과 같은 명령
SERVER = StdioServerParameters(
    command="uvx",
    args=["--from", "mcpdoc", "--with", "mcp<2", "mcpdoc",
          "--urls", "AgentDevelopmentKit:https://adk.dev/llms.txt",
          "--transport", "stdio"],
)


async def main() -> None:
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("[tools]", [t.name for t in tools.tools])

            # ① 등록된 문서 소스 (llms.txt 주소)
            res = await session.call_tool("list_doc_sources", {})
            print("[list_doc_sources]", res.content[0].text.strip())

            # ② llms.txt 색인 읽기: 코딩 에이전트는 여기서 필요한 페이지를 고른다
            res = await session.call_tool("fetch_docs", {"url": "https://adk.dev/llms.txt"})
            text = res.content[0].text
            print(f"[fetch_docs llms.txt] {len(text)}자")
            for line in text.splitlines():
                if "graphs/retry" in line or "coding-with-ai" in line:
                    print("   ", line.strip()[:120])

            # ③ 실제 문서 페이지 읽기 (예: 노드 재시도)
            res = await session.call_tool("fetch_docs", {"url": "https://adk.dev/graphs/retry/"})
            page = res.content[0].text
            print(f"[fetch_docs graphs/retry] {len(page)}자, 'max_attempts' 포함={('max_attempts' in page)}")


if __name__ == "__main__":
    asyncio.run(main())
