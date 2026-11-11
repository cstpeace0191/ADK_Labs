# my_agent — ADK CLI 기본 스캐폴딩 에이전트

이 문서는 Google ADK CLI의 `adk create` 명령어를 통해 자동 생성되는 기본 에이전트 프로젝트인 `my_agent`의 생성 배경, 폴더 구조, 런타임 동작 원리, 일반 실행 방법 및 실행 위치별 웹 인터페이스 차이점을 안내합니다.

---

## 1. 생성 배경 (`adk create`)

`my_agent` 폴더는 상위 폴더(`part03_cli/`)에서 아래 명령어를 실행하여 생성된 표준 스캐폴딩 프로젝트입니다.

```bash
cd part03_cli
adk create my_agent
```

* ADK CLI는 이 명령을 통해 에이전트 구동에 필요한 최소한의 파일 골격(`__init__.py`, `agent.py`, `.env`, `.gitignore`)을 자동으로 생성합니다.

---

## 2. 프로젝트 구조 및 파일 역할

```text
part03_cli/my_agent/
├── agent.py          # [자동 생성] root_agent 인스턴스 (LLM 모델, 이름, 기본 지시문 정의)
├── __init__.py       # [자동 생성] ADK Loader가 에이전트를 모듈로 인식하도록 노출 (from . import agent)
├── .env              # [자동 생성] 에이전트 전용 로컬 환경변수 파일
├── .gitignore        # [자동 생성] 버전 관리 제외 파일 정의
│
├── .adk/             # ⚡ [런타임 자동 생성] 에이전트 실행 시 생성되는 내부 세션 저장소
│   └── session.db    # 로컬 SQLite 세션 및 상태(State) 데이터베이스
│
└── README-KR.md      # ✍️ [수동 작성] adk create로 생성되지 않으며, 개발자가 직접 작성한 설명 문서
```

### 각 구성 요소의 생성 시점 및 특성

1. **`adk create`로 자동 생성되는 파일들**:
   * **`agent.py`**:
     * 에이전트의 핵심 코드로, Google ADK `Agent` 객체(`root_agent`)가 선언되어 있습니다.
     * 개발자는 이 파일에 지시문(instruction)을 보강하거나 도구(tools)를 등록하여 에이전트 기능을 확장합니다.
   * **`__init__.py`**:
     * `from . import agent` 한 줄로 구성되어 있으며, ADK CLI의 에이전트 로더(`AgentLoader`)가 이 폴더를 파이썬 패키지/에이전트로 인식할 수 있게 해줍니다.
   * **`.env`**:
     * 특정 에이전트만의 독립된 환경변수를 설정할 때 사용합니다. (상위 폴더에 공통 `.env`가 있다면 상위 파일이 자동 로드됩니다.)
   * **`.gitignore`**:
     * 로컬 세션 데이터나 임시 파일이 Git에 추적되지 않도록 방지합니다.

2. **`.adk/` 디렉터리 (런타임 생성)**:
   * `adk create` 시점에는 존재하지 않습니다.
   * 에이전트를 최초로 실행(`adk run my_agent` 또는 `adk web`)하는 **런타임(Runtime) 시점에 ADK 엔진에 의해 자동으로 생성**됩니다.
   * 내부의 `session.db`(SQLite)는 대화 메시지 이력, 세션 ID, State 변수들을 로컬에 안전하게 영속 보관합니다.

3. **`README-KR.md` (수동 작성)**:
   * `adk create` 명령은 프로젝트 설명 문서를 자동으로 만들어주지 않습니다.
   * 이 문서는 학습자 및 개발자가 에이전트의 구조와 사용법을 이해할 수 있도록 **수동으로 직접 작성된 문서**입니다.

---

## 3. 일반 실행 방법 (CLI Commands)

터미널 CLI 명령어는 일반적으로 **에이전트들의 상위 폴더(`part03_cli/`)**에서 실행하는 것이 표준입니다.

```bash
# 상위 폴더로 이동
cd part03_cli
```

### ① 기본 터미널 REPL 대화
터미널에서 즉시 에이전트와 대화를 나눕니다:
```bash
adk run my_agent
```

### ② 대화 세션 저장 (`--save_session`)
대화가 끝난 후 세션 내용을 JSON 파일로 저장하여, 이후 평가(eval) 데이터로 재활용할 수 있습니다:
```bash
adk run --save_session --session_id s1 my_agent
```
* 종료 시 `my_agent/s1.session.json` 파일이 생성됩니다.

### ③ 저장된 세션 재개 (`--resume`)
이전에 저장했던 대화 맥락을 이어서 진행합니다:
```bash
adk run --resume my_agent/s1.session.json my_agent
```

### ④ 대화 재생 모드 (`--replay`)
질문 목록이 담긴 JSON 입력 파일을 사람의 개입 없이 일괄 실행합니다:
```bash
adk run --replay queries.json my_agent
```

### ⑤ 웹 UI 개발 환경 실행 (`adk web`)
브라우저에서 대화, 이벤트 로그, 상태(State), 워크플로우 그래프를 시각적으로 확인합니다:
```bash
adk web --port 8000
```
* 브라우저에서 `http://localhost:8000` 접속 후 좌측 상단에서 `my_agent`를 선택합니다.

### ⑥ 헤드리스 REST/SSE 서버 실행 (`adk api_server`)
FastAPI 기반 백엔드 서비스로 에이전트를 호스팅합니다:
```bash
adk api_server --port 8000
```

---

## 4. 실행 위치에 따른 웹 인터페이스 차이 (`adk web --port 8000`)

`adk web` 명령을 **부모 폴더(`part03_cli`)**에서 실행하는가, 아니면 **에이전트 폴더(`my_agent`) 내부**에서 실행하는가에 따라 ADK 내부 로더 모드와 웹 인터페이스(UI) 구성이 달라집니다.

```
[경우 A] 부모 폴더(part03_cli)에서 실행             [경우 B] 에이전트 폴더(my_agent)에서 실행
       adk web --port 8000                                 adk web --port 8000
                 │                                                   │
                 ▼                                                   ▼
     [다중 에이전트 모드]                                    [단일 에이전트 모드]
 ┌───────────────────────────────┐                   ┌───────────────────────────────┐
 │ 웹 UI 좌측 상단 드롭다운 표시     │                   │ 웹 UI 에이전트 선택창 없음       │
 │   my-agents-cli               │                   │                               │
 │   my-agents-cli_mod           │                   │ (my_agent 화면으로 고정)        │
 │ ▼ my_agent                    │                   │                               │
 │   my_agent_mod                │                   │                               │
 │ (자유롭게 전환하며 테스트)       │                    │ (my_agent 단독 집중 테스트)     │
 └───────────────────────────────┘                   └───────────────────────────────┘
```

### 상세 비교 분석

| 비교 항목 | 부모 폴더(`part03_cli/`)에서 실행 | 해당 폴더(`my_agent/`) 내부에서 실행 |
|---|---|---|
| **실행 명령어** | `cd part03_cli && adk web --port 8000` | `cd part03_cli/my_agent && adk web --port 8000` |
| **ADK 내부 로딩 모드** | **다중 에이전트 모드** (`is_single_agent: False`) | **단일 에이전트 모드** (`is_single_agent: True`) |
| **웹 UI 에이전트 선택 메뉴** | 좌측 상단에 **드롭다운 선택창(Agent Selector) 제공** | **선택 메뉴 없음** (현재 에이전트로 잠금 고정) |
| **탐색 범위** | 현재 폴더 아래의 모든 서브폴더 에이전트 검색 (`my_agent`, `my_agent_mod` 등) | 현재 디렉터리의 `agent.py` 단 하나만 로드 |
| **에이전트 전환 가능 여부** | 드롭다운 클릭으로 자유롭게 에이전트 전환 가능 | 다른 에이전트로 전환 불가 (단독 대화 화면) |
| **주요 권장 상황** | 여러 에이전트를 비교하거나 전체 프로젝트를 총괄 테스트할 때 | 기본 스캐폴딩 동작 확인 및 프롬프트 디버깅에만 집중할 때 |

---

## 5. `my_agent` vs `my_agent_mod` 비교

* **`my_agent/`**:
  * `adk create my_agent` 명령으로 막 생성된 순수 스캐폴딩 상태의 기본 어시스턴트 에이전트입니다.
* **`my_agent_mod/`**:
  * `my_agent`의 기본 구조에 날씨 조회 도구(`get_weather`)와 상세 지시문을 추가하여 기능을 완성한 커스텀 에이전트 예제입니다.
