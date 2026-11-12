# my-agents-cli-mod

Real-time world clock & weather assistant (also answers general questions).
Agent generated with `agents-cli` version `1.13.0` (template `adk_python`) and customized in `app/agent.py`.

> 📄 Detailed guides: [README-KR.md](README-KR.md) (Korean) · [README-EN.md](README-EN.md) (English)

## Project Structure

```
my-agents-cli-mod/
├── app/                           # Core agent code (agent_directory)
│   ├── agent.py                   # root_agent "my_agents_cli_mod": geocode / get_current_time / get_weather
│   ├── fast_api_app.py            # FastAPI server: ADK web UI + REST/SSE + A2A (/a2a/app)
│   └── app_utils/                 # a2a.py, reasoning_engine_adapter.py, services.py
├── tests/                         # unit, integration, and eval (agents-cli eval run)
├── deployment/terraform/          # Terraform infrastructure (from `agents-cli scaffold enhance`)
├── generate_adk_web_ppt.py        # Generates ADK_Web_Architecture_Guide.pptx (python-pptx)
├── agents-cli-manifest.yaml       # agents-cli metadata (region us-east1, target agent_runtime)
├── Dockerfile                     # Container image (port 8080) — copies this README.md
├── GEMINI.md                      # AI-assisted development guide
└── pyproject.toml                 # Project dependencies
```

## Agent

- **Tools**: `geocode`, `get_current_time`, `get_weather` using the [Open-Meteo](https://open-meteo.com/) API (no API key needed).
- **Korean support**: Korean city names (e.g., 서울, 도쿄) are mapped to English; weather conditions are reported in Korean.
- **Offline fallback**: Set `AGENT_OFFLINE=1` (or lose network) to use built-in coordinates and default weather data.
- **Model**: `ADK_MODEL` env var (default `gemini-3.8-flash`).
- **Environment**: Loads `./.env` (if present) and the lab root `ADK_Labs/.env`.

## Requirements

- **uv**: [Install](https://docs.astral.sh/uv/getting-started/installation/)
- **agents-cli**: `uv tool install google-agents-cli`
- **Google Cloud SDK** (for deployment): [Install](https://cloud.google.com/sdk/docs/install)

## Quick Start

```bash
cd part03_cli/my-agents-cli-mod
agents-cli install          # Install dependencies
agents-cli playground       # Launch local web UI
```

Alternatives:

```bash
uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 --reload
uv run adk web --port 8008
uv run adk run app
```

## Commands

| Command | Description |
| --- | --- |
| `agents-cli install` | Install dependencies using uv |
| `agents-cli playground` | Launch local development environment |
| `agents-cli lint` | Run code quality checks |
| `agents-cli eval run` | Run and grade `tests/eval/datasets/basic-dataset.json` |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests |
| `agents-cli deploy` | Deploy agent to Agent Runtime (`us-east1`) |
| `agents-cli publish gemini` | Register deployed agent with Gemini |
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Upgrade template while preserving customizations |

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging (enabled with `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true`).

## A2A Inspector

This agent supports the [A2A Protocol](https://a2a-protocol.org/) at `/a2a/app`. Use the [A2A Inspector](https://github.com/a2aproject/a2a-inspector) to test interoperability.
