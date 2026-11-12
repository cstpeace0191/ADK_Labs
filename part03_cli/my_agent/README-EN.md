# my_agent — Basic ADK Agent

This is the standard and minimal Google ADK (Agent Development Kit) agent project scaffolded by the `adk create my_agent` command. It uses the LLM (Gemini) directly to answer general user questions without external custom tools.

---

## 1. Directory Structure

```text
my_agent/
├── agent.py          # 📄 [Core Code] Defines root_agent (Agent/LlmAgent declaration and prompt configuration)
├── __init__.py       # 📄 [Package Init] Module export for ADK loader (`from . import agent`)
├── .env              # ⚙️ [Environment] Model name (ADK_MODEL) and API key configuration
├── .gitignore        # ⚙️ [Git Config] Ignore rules for session DB and local cache
└── .adk/             # ⚡ [Runtime Generated] Data folder automatically created by ADK during local execution
    └── session.db    # ⚡ [Dynamically Generated] Local SQLite database storing conversation sessions
```

### Key Files and Roles
- **`agent.py`**: The main entry point for the agent. It defines `root_agent` with model (`gemini-3.5-flash`), agent name (`root_agent`), description, and system instructions.
- **`__init__.py`**: Exports the agent module (`from . import agent`) so that ADK's `AgentLoader` can discover and load the agent using just the folder name `my_agent`.
- **`.adk/session.db`**: SQLite database generated during execution (`adk run`, `adk web`, etc.) to persist conversation state across invocations.

---

## 2. How to Run

Execute the agent using `adk` CLI commands from the parent directory (`part03_cli`):

```bash
# 1. Navigate to parent directory (if not already there)
cd part03_cli

# 2. Run terminal interactive REPL
adk run my_agent

# 3. Run with in-memory session (no session.db created/used)
adk run --in_memory my_agent

# 4. Run and save session to a file (creates my_agent/s1.session.json upon exit)
adk run --save_session --session_id s1 my_agent

# 5. Resume from a saved session file
adk run --resume my_agent/s1.session.json my_agent

# 6. Launch web UI (open http://localhost:8000 in your browser)
adk web --port 8000

# 7. Launch headless REST / SSE API server
adk api_server --port 8000
```

