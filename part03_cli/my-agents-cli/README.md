# my-agents-cli

An enterprise-ready ReAct agent project scaffolded with `google-agents-cli` version `1.13.0`.  
It features a FastAPI-based backend, A2A (Agent-to-Agent) protocol support, Vertex AI Reasoning Engine adapter, automated test suites (unit, integration, eval), and Terraform infrastructure as code.

---

## 1. Directory Structure

```text
my-agents-cli/
├── app/                             # [Initial] Core agent application code
│   ├── agent.py                     # Main agent logic & mock tools (weather, current time)
│   ├── fast_api_app.py              # FastAPI server supporting REST, SSE, and A2A
│   ├── __init__.py                  # Python package initialization
│   ├── app_utils/                   # Agent helper utilities
│   │   ├── a2a.py                   # A2A protocol communication & Agent Card handling
│   │   ├── reasoning_engine_adapter.py # Vertex AI Reasoning Engine route adapter
│   │   └── services.py              # ADK session & artifact service factories
│   └── .adk/                        # ⚡ [Runtime Generated] Local session cache folder
│       └── session.db               # ⚡ Local SQLite database for session storage
│
├── deployment/                      # ⚡ [scaffold enhance] Cloud infrastructure code
│   └── terraform/                   # Terraform HCL definitions for Google Cloud
│       ├── shared/                  # Shared modules (BigQuery logging schema, etc.)
│       └── single-project/          # Single-project deployment scripts (service.tf, iam.tf)
│
├── tests/                           # Testing & evaluation suite
│   ├── unit/                        # Unit test suite
│   │   └── test_dummy.py            # Basic unit test sample
│   ├── integration/                 # Integration test suite
│   │   ├── test_agent.py            # Agent logic integration test
│   │   └── test_server_e2e.py       # FastAPI & SSE endpoint end-to-end tests
│   └── eval/                        # Agent evaluation pipeline
│       ├── eval_config.yaml         # Evaluation configuration and metrics
│       ├── response_quality.py      # LLM response quality automated scorer
│       └── datasets/                # Evaluation test cases
│           ├── basic-dataset.json   # Queries and ground-truth answers
│           └── README.md            # Dataset guidelines
│
├── .venv/                           # ⚡ [uv sync] Python virtual environment
├── .google-agents-cli/              # ⚡ [Runtime Generated] Local server execution logs
│   ├── run_server.log               # Server stdout log
│   └── run_server.stderr.log        # Server stderr log
│
├── agents-cli-manifest.yaml         # agents-cli project metadata
├── pyproject.toml                   # Project dependencies and configuration
├── uv.lock                          # Dependency lockfile
├── deployment_metadata.json         # ⚡ Remote Agent Engine ID & deployment record
├── Dockerfile                       # Container deployment definition
├── .env                             # Local environment variables (API keys, etc.)
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore rules
├── .gcloudignore                    # Google Cloud ignore rules
├── GEMINI.md                        # AI assistant context guide
├── README.md                        # English documentation (this file)
└── README-KR.md                     # Detailed Korean documentation
```

---

## 2. Requirements

Ensure you have the following tools installed:
- **uv**: Fast Python package manager - [Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)
- **agents-cli**: Google Agents CLI - install via `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Installation Guide](https://cloud.google.com/sdk/docs/install)

---

## 3. How to Run

Execute the following commands from within the `my-agents-cli` directory:

```bash
# 1. Navigate to the project directory
cd my-agents-cli

# 2. Install dependencies
agents-cli install

# 3. Launch local development playground (default port: 8000)
agents-cli playground

# 4. Directly run the FastAPI server with Uvicorn
uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 --reload

# 5. Run linter
agents-cli lint

# 6. Run unit and integration tests
uv run pytest tests/unit tests/integration

# 7. Run evaluation pipeline
agents-cli eval

# 8. Deploy to Google Cloud Agent Runtime
gcloud config set project <your-project-id>
agents-cli deploy

# 9. Register deployed agent with Gemini
agents-cli publish gemini
```

---

## 4. 🛠️ Project Management Commands

| Command | Action |
| :--- | :--- |
| `agents-cli scaffold enhance` | Adds CI/CD pipelines and Terraform infrastructure modules |
| `agents-cli infra cicd` | One-command setup for entire CI/CD pipeline and infrastructure |
| `agents-cli scaffold upgrade` | Upgrades template to the latest version while preserving user edits |

---

## 5. Request Processing Flow: Uvicorn to Agent

Based on `app/fast_api_app.py`, this diagram illustrates how incoming client requests flow into `root_agent`:

### 1) Server Boot
```bash
uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000
```
- `load_dotenv()` loads `.env` variables.
- `get_fast_api_app(...)` creates the FastAPI app with ADK web UI and standard API routes.
- Shared service instances are registered with `shared://session` and `shared://artifact` URIs.
- `attach_reasoning_engine_routes(app)` binds `/api/reasoning_engine` routes.

### 2) Lifespan: Server Startup Event
- Imports `adk_app` and `root_agent` from `app/agent.py`.
- Initializes `Runner(app=adk_app, session_service=..., artifact_service=...)` and stores it in `app.state.runner`.
- Binds A2A routes at `/a2a/app`.

### 3) Route Dispatch

| Request | Origin | Handler / Responsibility |
| :--- | :--- | :--- |
| `POST /run_sse` | ADK (`api_server.py`) | Primary streaming SSE endpoint used by ADK Web UI & playground |
| `POST /run` | ADK | Executes agent and returns all events as a single JSON array |
| `POST /a2a/app` (JSON-RPC) | `app_utils/a2a.py` | `A2aAgentExecutor` dispatches incoming A2A requests to Runner |
| `POST /api/reasoning_engine` | `app_utils/reasoning_engine_adapter.py` | Cloud console playground adapter |

### 4) `/run_sse` Execution Flow
```text
HTTP POST /run_sse (JSON payload)
  │
  ▼
api_server.run_agent_sse()
  │  get_runner_async("app")
  │    └─ Retrieves cached Runner instance
  ▼
Runner.run_async(user_id, session_id, new_message)
  │  1) Fetch or auto-create session in session_service
  │  2) Append new_message to session events
  │  3) Run plugin hooks and execute root_agent
  ▼
root_agent (LlmAgent "my_agents_cli")
  │  Calls Gemini with prompt and registered tools (get_weather, get_current_time)
  │  ├─ On tool request → triggers function_call, executes local tool, and feeds result back
  │  └─ On completion → returns final response text
  ▼
Stream each Event to client as an SSE ("data: {...}\n\n") chunk
```

---

## 6. Observability and A2A Protocol

- **Observability**: Built-in telemetry exports trace, logging, and metrics to Google Cloud Trace, Cloud Logging, and BigQuery.
- **A2A Protocol**: Fully compatible with [A2A Protocol](https://a2a-protocol.org/). Validate interoperability using [A2A Inspector](https://github.com/a2aproject/a2a-inspector).

