# Google ADK Lab Troubleshooting FAQ & Guide

This guide summarizes common issues and solutions encountered while working through the Google ADK hands-on labs (`ADK_Labs`).

---

## Table of Contents
1. [PowerShell Script Execution Policy Error](#1-powershell-script-execution-policy-error)
2. [Port (8000) Conflict Error](#2-port-8000-conflict-error)
3. [Gemini API Free Key Quota Exceeded (HTTP 429 / ResourceExhausted)](#3-gemini-api-free-key-quota-exceeded-http-429--resourceexhausted)
4. [`Eval module is not installed` Error When Running `adk eval`](#4-eval-module-is-not-installed-error-when-running-adk-eval)
5. [MCP Tool Import Error (part06_tools)](#5-mcp-tool-import-error-part06_tools)
6. [Human-in-the-Loop (HITL) Input Waiting and Resumption](#6-human-in-the-loop-hitl-input-waiting-and-resumption)
7. [`.env` Environment Variable Detection and Location Rules](#7-env-environment-variable-detection-and-location-rules)

---

### 1. PowerShell Script Execution Policy Error

#### Symptom
When activating the virtual environment (`.venv\Scripts\Activate.ps1`) in Windows PowerShell, the following security error occurs:
```text
.venv\Scripts\Activate.ps1 : File cannot be loaded because running scripts is disabled on this system.
```

#### Solution
Temporarily grant script execution permission for the current terminal session only:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```
> **Tip**: If you are using `uv`, you can bypass this error completely without activating the virtual environment by running `uv run <command>` (e.g., `adk web --port 8000`).

---

### 2. Port (8000) Conflict Error

#### Symptom
Running `adk web --port 8000` or `adk api_server --port 8000` fails with `[Errno 10048] error while attempting to bind on address` or `Address already in use`.

#### Cause
Windows IIS, another development server, or a background program is already occupying port 8000.

#### Solution
Switch to another unused port (e.g., **8008**, **8080**, **8888**) when running the command:
```bash
# When running adk web
adk web --port 8008

# When running adk api_server
adk api_server --port 8008
```
Then open `http://localhost:8008` in your browser.

---

### 3. Gemini API Free Key Quota Exceeded (HTTP 429 / ResourceExhausted)

#### Symptom
While running an agent, a `429 ResourceExhausted` or `Quota exceeded for quota metric...` error occurs.

#### Cause
- The Google AI Studio Free Tier enforces strict limits per model on **Requests Per Minute (RPM: ~5–15 requests)** and **Requests Per Day (RPD: ~20–50 requests)**.
- During multi-turn conversations, multi-agent setups, or workflow executions, even a single user query can trigger 2–4+ internal LLM API calls, quickly exhausting the quota.

#### Solution
1. **Automatic Retry Mechanism**:
   - `common/bootstrap.py` at the root of the lab repository includes built-in logic that automatically waits 10s → 20s → 40s and retries when a 429 error occurs. If you temporarily hit an RPM limit, simply wait a moment and execution will resume automatically.
2. **Switch Models**:
   - If your daily quota (RPD) is exhausted, retries will not resolve the issue. Change `ADK_MODEL` in your `.env` file to another free-tier model:
   ```ini
   # If gemini-3.5-flash-lite quota is exceeded -> switch to gemini-2.5-flash, etc.
   ADK_MODEL=gemini-2.5-flash
   ```
3. **Check Tool Restrictions**:
   - The `google_search` tool in `part06_tools` may be blocked on free API keys. This tool works reliably with a billing-enabled paid API key or in a Vertex AI environment.

---

### 4. `Eval module is not installed` Error When Running `adk eval`

#### Symptom
Even after activating the virtual environment, running `adk eval ...` fails with `Eval module is not installed`.

#### Cause
On Windows, another Python/ADK executable registered in the global system PATH (e.g., `C:\Python311\Scripts\adk.exe`) is invoked first, preventing it from referencing the `google-adk[eval]` package installed in the active virtual environment.

#### Solution
Invoke the module inside the virtual environment directly or use `uv run`:
```bash
# Method 1 (Recommended): Use uv run
adk eval weather_agent weather_agent/weather.evalset.json --config_file_path weather_agent/test_config.json --print_detailed_results

# Method 2: Invoke the module directly via python -m
python -m google.adk.cli eval weather_agent weather_agent/weather.evalset.json --config_file_path weather_agent/test_config.json --print_detailed_results
```

---

### 5. MCP Tool Import Error (part06_tools)

#### Symptom
Running MCP-related code in `part06_tools` fails with an `McpToolset` import error.

#### Cause
Google ADK 2.6.x is currently compatible with `mcp 1.x`. If a newer `mcp 2.x` version is installed, interface changes cause an import error.

#### Solution
Explicitly reinstall `mcp` 1.x as specified in `requirements.txt`:
```bash
uv pip install "mcp>=1.24,<2"
```

---

### 6. Human-in-the-Loop (HITL) Input Waiting and Resumption

#### Symptom
During `part09` · `part10` · `part13` labs, the script stops progressing after printing an `adk_request_input` or `adk_request_confirmation` event.

#### Explanation & Action
- **This is expected behavior**: A HITL (human intervention) node has been triggered and is waiting for user approval or input.
- **When running terminal scripts**: The `Session.resume_input()` function in `common/runner_util.py` passes the response based on the previous `interrupt_id` and automatically proceeds to the next step.
- **When running in the `adk web` UI**: A user input form or approve/reject buttons appear below the chat window in the browser. Submitting your response directly in that UI resumes the workflow.

---

### 7. `.env` Environment Variable Detection and Location Rules

#### Symptom
Even after entering your API key, `API key not found` or authentication errors occur.

#### Checklist
1. Verify that the file is named **`.env`**, not `.env.example`.
2. Ensure the key value is entered right after `GOOGLE_API_KEY=` without extra spaces or quotes:
   ```ini
   GOOGLE_GENAI_USE_VERTEXAI=FALSE
   GOOGLE_API_KEY=AIzaSy...
   ```
3. **Check `.env` settings for your authentication method**:
   - **When using a Google AI Studio API Key**:
     ```ini
     GOOGLE_GENAI_USE_VERTEXAI=FALSE
     GOOGLE_API_KEY=AIzaSy...
     ```
   - **When using Vertex AI** (requires running `gcloud auth application-default login` beforehand):
     ```ini
     GOOGLE_GENAI_USE_VERTEXAI=TRUE
     GOOGLE_CLOUD_PROJECT=your-gcp-project-id
     GOOGLE_CLOUD_LOCATION=asia-northeast3
     # GOOGLE_API_KEY= (disabled)
     ```
4. **Location Rule**: ADK automatically searches for a `.env` file starting from the current working directory and walking up parent directories. Therefore, placing a single `.env` file at the project root (`ADK_Labs/.env`) allows all `part02` through `part12` subfolders to share it automatically.

