# Google ADK 실습 트러블슈팅 FAQ 및 가이드

Google ADK 실습(`ADK_Labs`) 진행 중 자주 발생하는 문제와 해결 방법을 정리한 가이드입니다.

---

## 목차
1. [PowerShell 스크립트 실행 권한 오류](#1-powershell-스크립트-실행-권한-오류)
2. [포트(8000) 충돌 오류](#2-포트8000-충돌-오류)
3. [Gemini API 무료 키 한도 초과 (HTTP 429 / ResourceExhausted)](#3-gemini-api-무료-키-한도-초과-http-429--resourceexhausted)
4. [`adk eval` 실행 시 `Eval module is not installed` 에러](#4-adk-eval-실행-시-eval-module-is-not-installed-에러)
5. [MCP 도구 import 에러 (part06_tools)](#5-mcp-도구-import-에러-part06_tools)
6. [Human-in-the-Loop(HITL) 입력 대기 및 재개](#6-human-in-the-loophitl-입력-대기-및-재개)
7. [`.env` 환경 변수 인식 및 위치 규칙](#7-env-환경-변수-인식-및-위치-규칙)

---

### 1. PowerShell 스크립트 실행 권한 오류

#### 현상
Windows PowerShell에서 가상환경 활성화(`.venv\Scripts\Activate.ps1`) 시 다음과 같은 보안 에러 발생:
```text
.venv\Scripts\Activate.ps1 : 이 시스템에서 스크립트를 실행할 수 없으므로 파일을 로드할 수 없습니다.
```

#### 해결 방법
현재 터미널 세션에만 스크립트 실행 권한을 임시 부여합니다:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```
> **Tip**: `uv`를 사용할 경우 가상환경을 활성화하지 않고 `uv run <명령어>`(예: `adk web --port 8000`)를 사용하면 이 오류를 완전히 우회할 수 있습니다.

---

### 2. 포트(8000) 충돌 오류

#### 현상
`adk web --port 8000` 또는 `adk api_server --port 8000` 실행 시 `[Errno 10048] error while attempting to bind on address` 또는 `Address already in use` 발생.

#### 원인
Windows IIS, 개발 서버, 기타 백그라운드 프로그램이 이미 8000번 포트를 점유하고 있는 경우입니다.

#### 해결 방법
사용하지 않는 다른 포트(예: **8008**, **8080**, **8888**)로 포트를 변경하여 실행합니다:
```bash
# adk web 실행 시
adk web --port 8008

# adk api_server 실행 시
adk api_server --port 8008
```
브라우저에서도 `http://localhost:8008`로 접속하면 정상 동작합니다.

---

### 3. Gemini API 무료 키 한도 초과 (HTTP 429 / ResourceExhausted)

#### 현상
에이전트 실행 중 `429 ResourceExhausted` 또는 `Quota exceeded for quota metric...` 에러 발생.

#### 원인
- Google AI Studio 무료 티어(Free Tier)는 모델당 **분당 요청 수(RPM: 약 5~15회)** 및 **일일 요청 수(RPD: 20~50회)** 제한이 매우 낮게 설정되어 있습니다.
- 멀티턴 대화나 멀티 에이전트, 워크플로우 실행 시 한 번의 질문에도 내부적으로 2~4회 이상의 LLM API 호출이 발생하므로 금방 한도에 도달할 수 있습니다.

#### 해결 방법
1. **자동 재시도 메커니즘**:
   - 실습 코드 루트의 `common/bootstrap.py`에 429 에러 발생 시 자동으로 10초 → 20초 → 40초 대기 후 재시도하는 로직이 내장되어 있습니다. 일시적인 RPM 초과 시 잠시 기다리면 자동 재개됩니다.
2. **모델 전환**:
   - 일일 한도(RPD)가 소진된 경우 재시도로 해결되지 않습니다. `.env` 파일의 `ADK_MODEL`을 다른 무료 모델로 변경해 보세요:
   ```ini
   # gemini-3.5-flash-lite 한도 초과 시 -> gemini-2.5-flash 등으로 변경
   ADK_MODEL=gemini-2.5-flash
   ```
3. **도구 제약 확인**:
   - part06_tools의 `google_search` 도구는 무료 키 환경에서 차단될 수 있습니다. 해당 도구는 검색 전용 유료 결제 계정이나 Vertex AI 환경에서 원활히 동작합니다.

---

### 4. `adk eval` 실행 시 `Eval module is not installed` 에러

#### 현상
가상환경을 활성화했음에도 불구하고 `adk eval ...` 실행 시 `Eval module is not installed` 에러 발생.

#### 원인
Windows 환경에서 시스템 전역 PATH에 등록된 다른 Python/ADK 실행 파일(예: `C:\Python311\Scripts\adk.exe`)이 먼저 호출되어, 현재 가상환경에 설치된 `google-adk[eval]` 패키지를 참조하지 못하는 현상입니다.

#### 해결 방법
가상환경 내의 모듈을 직접 실행하거나 `uv run`을 사용합니다:
```bash
# 방법 1 (권장): uv run 사용
adk eval weather_agent weather_agent/weather.evalset.json --config_file_path weather_agent/test_config.json --print_detailed_results

# 방법 2: python -m 모듈 직접 호출
python -m google.adk.cli eval weather_agent weather_agent/weather.evalset.json --config_file_path weather_agent/test_config.json --print_detailed_results
```

---

### 5. MCP 도구 import 에러 (part06_tools)

#### 현상
`part06_tools`의 MCP 관련 코드 실행 시 `McpToolset` import 오류 발생.

#### 원인
Google ADK 2.6.x는 현재 `mcp 1.x` 버전과 호환됩니다. 만약 최신 `mcp 2.x` 버전이 설치된 경우 인터페이스 변경으로 인해 import 오류가 발생합니다.

#### 해결 방법
`requirements.txt`에 지정된 대로 mcp 1.x 버전을 명시적으로 재설치합니다:
```bash
uv pip install "mcp>=1.24,<2"
```

---

### 6. Human-in-the-Loop(HITL) 입력 대기 및 재개

#### 현상
part09 · part10 · part13 실습 중 스크립트가 더 이상 진행되지 않고 `adk_request_input` 또는 `adk_request_confirmation` 이벤트를 출력한 후 멈춥니다.

#### 설명 및 조치
- **정상 동작입니다**: HITL(사람 개입) 노드가 트리거되어 사용자 승인 또는 입력을 기다리는 상태입니다.
- **터미널 스크립트 실행 시**: `common/runner_util.py`의 `Session.resume_input()` 함수가 이전 `interrupt_id`를 기반으로 응답을 전달하여 자동으로 다음 단계를 진행합니다.
- **`adk web` UI 실행 시**: 브라우저 화면의 대화창 아래에 사용자 입력 폼이나 확인/거절 버튼이 활성화되므로, 해당 UI에서 직접 응답을 입력하고 전송하면 워크플로우가 재개됩니다.

---

### 7. `.env` 환경 변수 인식 및 위치 규칙

#### 현상
API 키를 입력했는데도 `API key not found` 또는 인증 오류가 발생합니다.

#### 확인 사항
1. 파일명이 `.env.example`이 아닌 **`.env`**인지 확인합니다.
2. `GOOGLE_API_KEY=` 뒤에 공백이나 따옴표 없이 키 값을 올바르게 입력했는지 확인합니다:
   ```ini
   GOOGLE_GENAI_USE_VERTEXAI=FALSE
   GOOGLE_API_KEY=AIzaSy...
   ```
3. **인증 방식별 `.env` 설정 확인**:
   - **Google AI Studio API 키 사용 시**:
     ```ini
     GOOGLE_GENAI_USE_VERTEXAI=FALSE
     GOOGLE_API_KEY=AIzaSy...
     ```
   - **Vertex AI 사용 시** (`gcloud auth application-default login` 사전 수행 필요):
     ```ini
     GOOGLE_GENAI_USE_VERTEXAI=TRUE
     GOOGLE_CLOUD_PROJECT=your-gcp-project-id
     GOOGLE_CLOUD_LOCATION=asia-northeast3
     # GOOGLE_API_KEY= (비활성화)
     ```
4. **위치 규칙**: ADK는 현재 작업 디렉터리에서 시작해 상위 디렉터리로 올라가며 `.env` 파일을 자동 탐색합니다. 따라서 프로젝트 루트(`ADK_Labs/.env`)에 하나만 두면 모든 `part02` ~ `part12` 하위 폴더에서 공통으로 인식됩니다.

