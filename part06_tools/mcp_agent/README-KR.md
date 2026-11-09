# mcp_agent — Model Context Protocol(MCP) 파일시스템 에이전트

Anthropic이 제창하고 업계 표준으로 자리잡은 **MCP(Model Context Protocol)** 서버와 연동하여, 표준 프로토콜 기반으로 로컬 파일시스템을 탐색하고 읽는 에이전트입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent` (`file_assistant`)
- **연동 MCP 서버**:
  - `npx -y @modelcontextprotocol/server-filesystem [data/reports]`
  - Stdio(표준 입출력) 채널을 통해 Node.js 기반 MCP 서버 프로세스를 자식 프로세스로 구동
- **최소 권한 원칙 (`tool_filter`)**:
  ```python
  fs_tools = McpToolset(
      ...,
      tool_filter=["read_text_file", "read_file", "list_directory"],
  )
  ```
  파일 쓰기/삭제 도구는 제외하고, 조회 관련 도구만 에이전트에 노출하여 안전성을 확보합니다.

---

## 2. 사전 요구 사항 및 실행 방법

1. **사전 요구 사항**:
   - Node.js (`npx` 명령 실행 가능해야 함)
   - `mcp` 1.x 버전 (`uv pip install "mcp>=1.24,<2"`)
2. **실행 명령 (`part06_tools` 폴더)**:
   ```bash
   cd part06_tools
   uv run run_tools.py mcp
   ```

### 대상 파일 위치
`part06_tools/data/reports/` 폴더 안의 `q3_sales.md` 및 `team_notice.txt` 파일을 읽어 답변합니다.


