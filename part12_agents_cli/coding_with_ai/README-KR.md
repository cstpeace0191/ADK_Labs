# Coding with AI: 코딩 에이전트에게 ADK 전문성 주기

강의노트 Part 12 "Coding with AI" 두 장(슬라이드 128–129)과 짝을 이루는 설정 실습이다.
원문: [adk.dev/tutorials/coding-with-ai](https://adk.dev/tutorials/coding-with-ai/)

AI 코딩 도구(Antigravity · Claude Code · Cursor 등)에 ADK 지식을 주는 방법은 세 가지다.

| 방법 | 무엇을 주나 | 설정 |
|---|---|---|
| Agents CLI 스킬 | "어떻게 만들지": 개발 수명주기·스캐폴딩·평가·배포·관측 절차 | `uvx google-agents-cli setup` |
| ADK Docs MCP 서버 | "최신 API가 무엇인지": 문서 검색·읽기 도구 | 아래 `mcp.json` |
| ADK Docs Index | 기계가 읽는 문서 파일 | [llms.txt](https://adk.dev/llms.txt) · [llms-full.txt](https://adk.dev/llms-full.txt) |

## 1. Agents CLI 스킬 설치

```bash
uvx google-agents-cli setup
```

설치되는 스킬은 다음과 같다.
- 개발 수명주기와 코딩 가이드
- 프로젝트 스캐폴딩
- 평가 방법론과 점수
- Agent Runtime · Cloud Run · GKE 배포
- Gemini Enterprise 게시
- 트레이스 · 로깅 · 통합
- Python API 빠른 참조와 문서 색인

## 2. ADK Docs MCP 서버 연결

`uv`(uvx)가 필요하다. 서버는 [mcpdoc](https://pypi.org/project/mcpdoc/)이고, `adk.dev/llms.txt`를 읽어 다음 두 도구를 제공한다.
- `list_doc_sources`: 등록된 문서 소스 목록
- `fetch_docs`: 지정한 문서 페이지 읽기

### Claude Code

```bash
claude mcp add adk-docs --transport stdio -- uvx --from mcpdoc --with "mcp<2" mcpdoc --urls AgentDevelopmentKit:https://adk.dev/llms.txt --transport stdio
```

### Antigravity · Cursor · 그 밖의 MCP 지원 도구

[`mcp.json`](mcp.json)의 내용을 각 도구의 MCP 설정 파일에 넣는다.
- Antigravity: 에이전트 패널 `...` → MCP store → Manage MCP Servers → View raw config → `mcp_config.json`
- Cursor: Settings → Tools & MCP → New MCP Server → `mcp.json`

`mcp<2` 제약을 두는 이유는 mcpdoc이 MCP 1.x의 FastMCP API를 쓰기 때문이다. part06 MCP 실습에서 `mcp` 1.x를 요구하는 것과 같은 이유다.

## 3. 서버 동작 확인 (선택)

코딩 에이전트가 하는 MCP 호출(initialize → tools/list → tools/call)을 직접 해 본다.

```bash
uv run --no-project --with "mcp<2" check_mcpdoc.py
```

정상이면 다음이 출력된다.
- 도구 목록: `list_doc_sources`, `fetch_docs`
- `llms.txt` 색인의 일부
- `graphs/retry` 페이지 본문 길이

> 이 스크립트는 PyPI에서 mcpdoc을 내려받아 실행한다. 강의 PC에서는 외부 코드 실행 권한 때문에 실행 검증을 하지 않았다. 학생 PC에서 처음 실행할 때 결과를 확인한다.

## 4. 써 보기

MCP를 연결한 코딩 에이전트에 다음처럼 요청해 본다.
- "ADK 문서를 찾아서 이 Workflow의 fetch 노드에 RetryConfig를 걸어 줘"
- "adk.dev 문서 기준으로 이 에이전트를 Cloud Run에 배포하는 명령을 알려 줘"

에이전트는 문서 MCP로 `llms.txt`를 읽고 관련 페이지를 고른 뒤 그 내용을 근거로 코드를 쓴다.
