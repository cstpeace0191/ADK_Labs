# direct-adk-fastapi-client — Operational Architecture & Workflow Guide

This document details the operational architecture and conversational workflow of [`direct-adk-fastapi-client.py`](./direct-adk-fastapi-client.py), a lightweight interactive REPL client that connects to [`direct-adk-fastapi-server.py`](./direct-adk-fastapi-server.py) over HTTP.

---

## 1. Overview & Core Concepts

[`direct-adk-fastapi-client.py`](./direct-adk-fastapi-client.py) is a standalone command-line REPL (Read-Eval-Print Loop) client written in Python. It allows developers and users to interactively test and converse with the FastAPI-backed ADK agent without needing a web browser or frontend UI framework.

> **Key Capabilities**
> - **Pre-Flight Health Verification (`check_server_health`)**: Checks `/health` on the server before entering the prompt loop, guiding the user if the server is offline.
> - **Session Management & Context Tracking (`create_session` & `session_id`)**: Acquires an active session ID from the server's `/sessions` endpoint and maintains it across multiple conversational turns to preserve conversational context.
> - **Interactive REPL Loop**: Displays thinking status ("Agent is thinking..."), ignores empty inputs, and safely handles termination keywords (`quit`, `exit`, `q`) and keyboard interrupts (`Ctrl+C`).

---

## 2. System Architecture & Communication Flow

```mermaid
flowchart TD
    subgraph Client["Interactive Client (direct-adk-fastapi-client.py)"]
        START([Start Program])
        HEALTH["1. Pre-Flight Health Check<br>(check_server_health)"]
        CREATE_SESS["2. Initialize Session<br>(create_session)"]
        REPL["3. Wait for User Input<br>(input)"]
        SEND["4. Dispatch Chat Message<br>(send_chat_message)"]
        PRINT["5. Render Agent Response"]
        END_CHECK{"Exit Command?<br>(quit / exit / q)"}
        EXIT([Terminate Program])

        START --> HEALTH
        HEALTH -- "Server Reachable (200 OK)" --> CREATE_SESS
        HEALTH -- "Server Unreachable" --> EXIT
        CREATE_SESS --> REPL
        REPL --> END_CHECK
        END_CHECK -- "Exit Detected" --> EXIT
        END_CHECK -- "Message Prompt" --> SEND
        SEND --> PRINT
        PRINT --> REPL
    end

    subgraph Server["FastAPI Server (direct-adk-fastapi-server.py)"]
        H_EP["GET /health"]
        S_EP["POST /sessions"]
        C_EP["POST /chat"]
    end

    HEALTH -.->|HTTP GET| H_EP
    CREATE_SESS -.->|HTTP POST| S_EP
    SEND -.->|HTTP POST| C_EP
```

---

## 3. Conversational Interaction Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Terminal)
    participant Client as direct-adk-fastapi-client.py
    participant Server as FastAPI Server (127.0.0.1:8000)

    Note over User,Server: [Phase 1: Pre-Flight Health Check]
    User->>Client: Execute python direct-adk-fastapi-client.py
    Client->>Server: GET /health (timeout=5s)
    Server-->>Client: 200 OK {"status": "healthy", "agent": "weather_and_time_agent"}

    Note over User,Server: [Phase 2: Session Initialization]
    Client->>Server: POST /sessions {"user_id": "user01"}
    Server-->>Client: 200 OK {"session_id": "session_a1b2c3d4", "status": "created"}
    Client->>User: Display Banner & Active Session ID (session_a1b2c3d4)

    Note over User,Server: [Phase 3: Turn 1 (Seoul Weather Inquiry)]
    User->>Client: 🧑 You: "What's the weather in Seoul?"
    Client->>User: 🤖 Agent is thinking...
    Client->>Server: POST /chat {"message": "What's the weather in Seoul?", "session_id": "session_a1b2c3d4", "user_id": "user01"}
    Server-->>Client: 200 OK {"response": "The weather in Seoul is Clear sky, 3.2°C...", "session_id": "session_a1b2c3d4"}
    Client->>User: 🤖 Agent: The weather in Seoul is Clear sky, 3.2°C...

    Note over User,Server: [Phase 4: Turn 2 Multi-Turn Dialogue (Context Tracking)]
    User->>Client: 🧑 You: "What time is it there?"
    Client->>User: 🤖 Agent is thinking...
    Client->>Server: POST /chat {"message": "What time is it there?", "session_id": "session_a1b2c3d4", "user_id": "user01"}
    Note right of Server: Resolves 'there' = 'Seoul' using historical session events
    Server-->>Client: 200 OK {"response": "The current time in Seoul is 16:30 KST.", "session_id": "session_a1b2c3d4"}
    Client->>User: 🤖 Agent: The current time in Seoul is 16:30 KST.

    Note over User,Server: [Phase 5: Session Termination]
    User->>Client: 🧑 You: "exit"
    Client->>User: Ending session. Goodbye!
```

---

## 4. Key Functions Implementation Breakdown

### 1) `check_server_health(base_url: str) -> bool`
Validates connectivity with the FastAPI server before launching the interactive prompt loop:
```python
def check_server_health(base_url: str) -> bool:
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        return resp.status_code == 200
    except requests.RequestException:
        return False
```

### 2) `create_session(base_url: str, user_id: str) -> str`
Requests an official session from the server. If the server does not respond, it falls back to `"default_session"` gracefully:
```python
def create_session(base_url: str, user_id: str) -> str:
    try:
        resp = requests.post(f"{base_url}/sessions", json={"user_id": user_id}, timeout=5)
        if resp.status_code == 200:
            return resp.json().get("session_id")
    except requests.RequestException:
        pass
    return "default_session"
```

### 3) `send_chat_message(base_url, message, session_id, user_id) -> tuple[str, str]`
Dispatches a structured JSON payload to `/chat` and returns the synthesized response text alongside the verified `session_id`:
```python
def send_chat_message(base_url: str, message: str, session_id: str, user_id: str) -> tuple[str, str]:
    payload = {
        "message": message,
        "session_id": session_id,
        "user_id": user_id,
    }
    resp = requests.post(f"{base_url}/chat", json=payload, timeout=60)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("response", "(No response)"), data.get("session_id", session_id)
    else:
        return f"[Server Error {resp.status_code}]: {resp.text}", session_id
```

---

## 5. Execution & Usage Guide

### 1) Start the Server (Terminal 1)
```bash
# Execute from part02_architecture directory
uv run Direct_ADK/direct-adk-fastapi-server.py
```

### 2) Run the Client (Terminal 2)
```bash
# Execute from part02_architecture directory
uv run Direct_ADK/direct-adk-fastapi-client.py
```

Alternatively, override the target server URL using the `SERVER_URL` environment variable:
```bash
SERVER_URL="http://192.168.0.10:8000" python Direct_ADK/direct-adk-fastapi-client.py
```

### 3) Sample Conversation Output
```text
=================================================================
  💬 ADK Agent FastAPI Interactive Client
  Target Server: http://127.0.0.1:8000
=================================================================
  Active Session : session_4c8d19a2
  Commands       : Type 'quit', 'exit', or 'q' to end.
  Capabilities   : Weather, time, and general QA (multi-turn chat)
=================================================================

🧑 You: Current time and weather in Tokyo?
🤖 Agent: In Tokyo, the current local time is 2026-11-19 16:30 JST.
The weather is Clear sky with a temperature of 14.5°C, humidity of 48%, and wind speed of 2.1 m/s.

🧑 You: What about Paris?
🤖 Agent: In Paris, the current local time is 2026-11-19 08:30 CET.
The weather is Overcast with a temperature of 7.2°C, humidity of 85%, and wind speed of 3.4 m/s.

🧑 You: q
Ending session. Goodbye!
```

---

## 6. Related File Links
- 📄 [direct-adk-fastapi-client.py](./direct-adk-fastapi-client.py): Interactive client source code
- 📄 [direct-adk-fastapi-server.py](./direct-adk-fastapi-server.py): Backend FastAPI server source code
- 📄 [direct-adk-fastapi-server-workflow-README-EN.md](./direct-adk-fastapi-server-workflow-README-EN.md): Server operational workflow guide

