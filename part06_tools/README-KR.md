# part06_tools — ADK Tools (도구 확장과 통합)

> 강의노트 **Part 6 · 06. Tools: 에이전트의 손과 발** (슬라이드 70–77)과 짝을 이룬다. Skills(SkillToolset)는 Part 5 → [`../part05_skills/`](../part05_skills/README-KR.md)

Google ADK에서 에이전트가 외부 세계와 상호작용하는 5가지 도구 패턴(**Function Tool + Context/Confirmation**, **AgentTool**, **MCP**, **OpenAPI**, **Long Running Tool**)을 다룹니다.

---

## 1. 폴더 구조 및 서브 에이전트

```text
part06_tools/
├── shop_agent/          # ToolContext(장바구니 State 조작) + 결제 전 사용자 확인(require_confirmation)
├── analyst_agent/       # AgentTool: 다른 에이전트(코드 실행기, 웹 검색기)를 도구로 등록
├── mcp_agent/           # McpToolset: Model Context Protocol 파일시스템 서버 연동 (Node.js 필요)
├── openapi_agent/       # OpenApiToolset: hr_api.yaml 기반 REST API 자동 도구화 (+ 목업 서버)
├── refund_agent/        # LongRunningFunctionTool: 비동기 결재/승인 대기 도구 패턴
├── data/reports/        # mcp_agent 실습용 샘플 텍스트/마크다운 파일
├── run_tools.py         # 🔑 part06 통합 실습 러너 (shop · analyst · mcp · openapi · refund)
└── README-KR.md            # 현재 문서
```

---

## 2. 도구별 핵심 개념 및 특징

| 서브폴더 | 핵심 도구 클래스 | 주요 메커니즘 |
|---|---|---|
| **shop_agent** | `FunctionTool` | `ToolContext`를 통해 세션 `state['cart']` 변경, `require_confirmation=True`로 결제 전 이벤트 발행 |
| **analyst_agent** | `AgentTool` | 서브 에이전트(`searcher`, `calculator`)를 함수처럼 호출하여 계산 및 검색 위임 |
| **mcp_agent** | `McpToolset` | 앤스로픽 표준 MCP 서버(`@modelcontextprotocol/server-filesystem`)와 Stdio 통신 |
| **openapi_agent** | `OpenApiToolset` | OpenAPI 3.0 사양서(`hr_api.yaml`)를 읽어 REST API 엔드포인트를 함수 도구로 자동 변환 |
| **refund_agent** | `LongRunningFunctionTool` | 실행 즉시 결과를 내지 않고 `invocation_id`를 반환한 뒤 나중에 승인 결과 주입 |

---

## 3. 실행 방법

모든 명령은 `part06_tools` 폴더에서 실행합니다.

### ① 통합 러너 실행 (🔑 Gemini 키 필요)
```bash
cd part06_tools

# 전체 도구 순차 실행
uv run run_tools.py all

# 특정 도구만 선택 실행
uv run run_tools.py shop
uv run run_tools.py analyst
uv run run_tools.py refund
```

### ② 외부 서버가 필요한 도구 실행

#### 1) OpenAPI 도구 (`openapi_agent`)
목업 HR 서버를 먼저 띄운 후 실행합니다:
```bash
# 터미널 1: 목업 서버 기동 (포트 8000)
uv run openapi_agent/hr_mock_server.py

# 터미널 2: 에이전트 실행
uv run run_tools.py openapi
```

#### 2) MCP 파일시스템 도구 (`mcp_agent`)
Node.js(`npx`)가 설치되어 있어야 합니다:
```bash
uv run run_tools.py mcp
```
> ⚠ **MCP 버전 주의**: ADK 2.6은 `mcp 1.x`와 호환됩니다. 문제 발생 시 `uv pip install "mcp>=1.24,<2"`를 실행합니다.

### ③ 대화형 인터페이스 (`adk web` / `adk run`)
```bash
# 쇼핑 에이전트 대화 실행
adk run shop_agent

# 웹 개발 UI 실행 (http://localhost:8000)
adk web --port 8000
```



