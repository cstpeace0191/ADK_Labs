# adk-based_Agent — Google ADK Agent Project Collection

This project directory contains standard agent packages built with the **Google Agent Development Kit (ADK)**. Each agent is structured as an independent Python package following ADK specification, ready to run and test via terminal CLI, web GUI, or programmatic Runners.

---

## 1. Included Agent Folders

| Folder | Agent Role | Core Architecture & Tools | Key Learning Points |
|---|---|---|---|
| [**`chat_time_weather_agent`**](./chat_time_weather_agent/README-EN.md) | World city time & weather assistant and general chatter | Open-Meteo API integration, `geocode`, `get_current_time`, `get_weather`, offline fallback DB | • Tool auto-routing vs direct LLM response branch<br>• IANA Timezone and WMO weather code resolution<br>• PEP 8 & `AgentLoader` compliant folder design |
| [**`memory_layers_agent`**](./memory_layers_agent/README-EN.md) | Dual-layer memory (Short-term Session vs Long-term Memory) assistant | Session State (`user:name`, `trip`), Memory Service (`preload_memory`, `load_memory`) | • Session State prefix (`user:`, `temp:`, unqualified) scopes<br>• Prompt injection via `{key?}` template substitution<br>• Cross-session persistent knowledge accumulation & retrieval |

---

## 2. Directory Structure

```text
adk-based_Agent/
├── chat_time_weather_agent/          # Time, weather, and general conversation agent
│   ├── __init__.py                  # Exposes agent module and root_agent
│   ├── agent.py                     # Tool implementations and agent definition
│   ├── README-KR.md                 # Korean detailed documentation
│   └── README-EN.md                 # English detailed documentation
├── memory_layers_agent/             # Dual-layer memory agent
│   ├── __init__.py                  # Exposes agent module and root_agent
│   ├── agent.py                     # State tools and root_agent definition
│   ├── README-KR.md                 # Korean detailed documentation
│   └── README-EN.md                 # English detailed documentation
├── README-KR.md                     # Comprehensive Korean guide for the project
└── README-EN.md                     # Comprehensive English guide (this document)
```

---

## 3. Prerequisites and Configuration

### 1) Package Installation
Install Google ADK and required libraries in a Python 3.10+ environment:

```bash
pip install google-adk python-dotenv
# or using uv
uv pip install google-adk python-dotenv
```

### 2) Environment Variables (`.env`) Configuration
Create a `.env` file in the parent folder (`part02_architecture` or workspace root):

```env
# Gemini Developer API Key (Default)
GEMINI_API_KEY=your_gemini_api_key_here

# Or when using Google Cloud Vertex AI
# GOOGLE_GENAI_USE_VERTEXAI=TRUE
# GOOGLE_CLOUD_PROJECT=your-gcp-project-id
# GOOGLE_CLOUD_LOCATION=us-central1

# Default Agent model (Optional)
ADK_MODEL=gemini-flash-latest

# Offline testing mode (0: online API, 1: built-in offline data)
AGENT_OFFLINE=0
```

---

## 4. Execution and Testing Methods

The agents in this project can be executed at three different levels:

### Method 1: ADK CLI Interactive Mode (`adk run`)
Chat directly with the agents in your terminal:

```bash
# Run from within the adk-based_Agent directory

# 1) Run Time & Weather Agent
adk run chat_time_weather_agent

# 2) Run Dual-Layer Memory Agent
adk run memory_layers_agent
```

### Method 2: ADK Web Development UI (`adk web`)
Test visually in your browser using Google ADK's official web UI:

```bash
# Launch web server from within the adk-based_Agent directory
adk web --port 8008
```
Open `http://localhost:8008` in your browser, select your target agent (`chat_time_weather_agent` or `memory_layers_agent`) from the top-left dropdown, and start chatting.

### Method 3: Direct_ADK Integration Scripts
Observe internal event lifecycles and memory transitions in code using the test scripts located in the parent directory:

```bash
# Navigate to part02_architecture directory
cd ..

# 1) Observe request event lifecycle for chat_time_weather_agent
uv run Direct_ADK/run_events.py

# 2) Run dual-layer memory tests for memory_layers_agent (offline structure / Gemini integration)
uv run Direct_ADK/run_memory_layers.py offline
uv run Direct_ADK/run_memory_layers.py llm
uv run Direct_ADK/run_memory_layers.py all
```

---

## 5. Detailed Documentation Links
For detailed tool signatures, instruction prompt engineering, dialogue scenarios, and troubleshooting, please refer to the documentation in each folder:

- [chat_time_weather_agent Guide (Korean: README-KR.md)](./chat_time_weather_agent/README-KR.md) / [English (README-EN.md)](./chat_time_weather_agent/README-EN.md)
- [memory_layers_agent Guide (Korean: README-KR.md)](./memory_layers_agent/README-KR.md) / [English (README-EN.md)](./memory_layers_agent/README-EN.md)

