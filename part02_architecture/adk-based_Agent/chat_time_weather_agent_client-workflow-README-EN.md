# chat_time_weather_agent_client — Operational Architecture & Workflow Guide

This document provides a comprehensive architectural and operational guide for interacting with Google Agent Development Kit's (ADK) official HTTP server (**`adk api_server`**) using the interactive console client [`chat_time_weather_agent_client.py`](./chat_time_weather_agent_client.py).

---

## 1. Overview & Core Concepts

`chat_time_weather_agent` is an ADK-based agent designed to query real-time weather and current local time for global cities via the Open-Meteo API. By serving this agent as a microservice using `adk api_server`, users and applications can interact with it over HTTP. [`chat_time_weather_agent_client.py`](./chat_time_weather_agent_client.py) serves as an interactive terminal client that demonstrates multi-turn session tracking, real-time tool invocation inspection, and SSE streaming.

> **Key Components**
> - **`adk api_server`**: A FastAPI-based REST/SSE microservice server provided by Google ADK. Responsible for agent execution endpoints (`/run`, `/run_sse`), session lifecycle management, and artifact/memory servicing.
> - **`chat_time_weather_agent_client.py`**: An interactive terminal client that accepts user console input, sends structured requests to `adk api_server`, parses agent events in real time, and renders tool execution details and text responses.
> - **REST Sync (`/run`) vs SSE Streaming (`/run_sse`)**: Supports both full-event JSON array delivery upon turn completion and progressive Server-Sent Events streaming (`data: {...}`).

---

## 2. System Architecture

```mermaid
flowchart LR
    subgraph Client["Interactive Terminal Client (chat_time_weather_agent_client.py)"]
        CLI["User Console REPL (Input/Output Loop)"]
        PARSER["Event Parser (Tool Call / Text Dispatcher)"]
        HTTP["HTTP Client (requests)"]
        CLI --> HTTP
        HTTP --> PARSER
        PARSER --> CLI
    end

    subgraph Server["Google ADK Backend (adk api_server)"]
        API["FastAPI Endpoints (/health, /sessions, /run, /run_sse)"]
        RUNNER["ADK Runner Engine"]
        SESS["Session Service (Session State Store)"]
        API --> RUNNER
        RUNNER <--> SESS
    end

    subgraph AgentSystem["Agent Package (chat_time_weather_agent)"]
        AGENT["root_agent (gemini-3.8-flash)"]
        TOOLS["Open-Meteo Tools (geocode, get_weather, get_current_time)"]
        AGENT <--> TOOLS
    end

    subgraph External["External Services"]
        GEMINI["Google Gemini / Vertex AI"]
        METEO["Open-Meteo Weather & Geocoding API"]
    end

    HTTP <== "REST / SSE Communication" ==> API
    RUNNER <--> AGENT
    AGENT <--> GEMINI
    TOOLS <--> METEO
```

---

## 3. Session & Turn Execution Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Terminal)
    participant Client as chat_time_weather_agent_client
    participant Server as adk api_server (FastAPI)
    participant Agent as chat_time_weather_agent
    participant LLM as Gemini LLM
    participant Tool as Open-Meteo Tool

    Note over User,Server: [Phase 1: Connectivity Verification & Session Creation]
    Client->>Server: GET /health
    Server-->>Client: 200 OK (Server online)
    Client->>Server: GET /list-apps
    Server-->>Client: ["chat_time_weather_agent", "memory_layers_agent"]
    Client->>Server: POST /apps/chat_time_weather_agent/users/user_01/sessions/session_xxx
    Server-->>Client: 200 OK (Session created with fresh state)

    Note over User,Tool: [Phase 2: Turn 1 Conversation (Seoul Weather Query)]
    User->>Client: "What's the weather in Seoul?"
    Client->>Server: POST /run (appName, userId, sessionId, newMessage)
    Server->>Agent: Route message & load session context
    Agent->>LLM: Forward prompt & evaluate tool calls
    LLM-->>Agent: FunctionCall(name="get_weather", args={"location": "Seoul"})
    Agent->>Tool: Execute get_weather("Seoul")
    Tool-->>Agent: {"status": "success", "temperature": 3.2, "condition": "Clear", ...}
    Agent->>LLM: Pass tool response & request final answer synthesis
    LLM-->>Agent: "The current weather in Seoul is Clear (3.2°C)..."
    Server-->>Client: 200 OK [Event-1 (Tool Call), Event-2 (Tool Resp), Event-3 (Final Text)]
    Client->>User: ⚙️ [Tool Call] get_weather(location="Seoul")<br>🤖 [Agent]: The current weather in Seoul is Clear...

    Note over User,Tool: [Phase 3: Turn 2 Multi-Turn Conversation (Pronoun Context Tracking)]
    User->>Client: "What time is it there?"
    Client->>Server: POST /run (Reusing same sessionId)
    Server->>Agent: Inject session history ("there" refers to "Seoul")
    Agent->>LLM: Resolve context: "there" = "Seoul"
    LLM-->>Agent: FunctionCall(name="get_current_time", args={"location": "Seoul"})
    Agent->>Tool: Execute get_current_time("Seoul")
    Tool-->>Agent: {"status": "success", "current_time": "16:20 KST", ...}
    Agent->>LLM: Request final answer synthesis
    LLM-->>Agent: "The current local time in Seoul is 16:20 KST."
    Server-->>Client: 200 OK [Event array]
    Client->>User: ⚙️ [Tool Call] get_current_time(location="Seoul")<br>🤖 [Agent]: The current local time in Seoul is...
```

---

## 4. Key Endpoints & Protocol Specifications

### 1) Health Check & App Discovery
* **`GET /health`**
  - Verifies HTTP connectivity with the server. If unreachable, the client displays startup troubleshooting advice and safely exits.
* **`GET /list-apps`**
  - Retrieves the list of active agent applications served by the server.
  - Example response: `["chat_time_weather_agent", "memory_layers_agent"]`
  - The client verifies that the requested `--app` exists, or auto-binds to the single available agent.

### 2) Session Initialization
* **`POST /apps/{app_name}/users/{user_id}/sessions/{session_id}`**
  - Request body: `{"state": {}}`
  - Initializes a persistent session ID so message events and session state are tracked across multiple dialogue turns.
  - Response body:
    ```json
    {
      "id": "session_07aca660",
      "appName": "chat_time_weather_agent",
      "userId": "user_01",
      "state": {},
      "events": [],
      "lastUpdateTime": 1795072578.73
    }
    ```

### 3) Turn Execution (REST /run vs SSE /run_sse)
* **Request Payload (Shared `RunAgentRequest`)**:
  ```json
  {
    "appName": "chat_time_weather_agent",
    "userId": "user_01",
    "sessionId": "session_07aca660",
    "newMessage": {
      "role": "user",
      "parts": [{"text": "What's the weather in Seoul?"}]
    }
  }
  ```

* **Synchronous REST Mode (`POST /run`)**:
  - Waits until the agent loop finishes, returning the full array of execution events (`list[Event]`) in a single JSON payload.
* **Streaming SSE Mode (`POST /run_sse`)**:
  - Uses `Content-Type: text/event-stream`. As each tool call or text token is emitted by the agent, lines prefixed with `data: {...}\n\n` are sent to the client progressively.

---

## 5. Event Parsing & Rendering Mechanism

`chat_time_weather_agent_client.py` examines the `content.parts` array in each received `Event` and dispatches based on the part type:

```python
for p in parts:
    # 1. Tool / Function Call Event
    if "functionCall" in p:
        fc = p["functionCall"]
        print(f"  ⚙️  [Tool Call] {fc['name']}({json.dumps(fc.get('args'))})")

    # 2. Tool Execution Output Event
    elif "functionResponse" in p and self.verbose:
        fr = p["functionResponse"]
        print(f"  📥 [Tool Resp] {fr['name']} -> {fr.get('response')}")

    # 3. Agent Conversational Text Event
    elif "text" in p and p.get("text"):
        print(f"\n🤖 [{author}]:\n{p['text'].strip()}")
```

---

## 6. Execution & Usage Guide

### 1) Start the Server (Terminal 1)
```bash
# Start api_server from the adk-based_Agent folder
cd part02_architecture/adk-based_Agent
adk api_server --port 8000
```

### 2) Launch the Client (Terminal 2)
```bash
# Run in default synchronous REST mode
python chat_time_weather_agent_client.py

# Run in SSE streaming mode
python chat_time_weather_agent_client.py --stream

# Run against a custom host or user identifier
python chat_time_weather_agent_client.py --url http://127.0.0.1:8000 --user guest_01
```

### 3) In-Chat Slash (/) Commands
| Command | Description |
|---|---|
| `/new` or `/reset` | Terminate the active session and create a fresh `session_id` |
| `/stream` | Toggle between REST sync mode (`/run`) and SSE streaming mode (`/run_sse`) |
| `/apps` | List all registered agent applications on the server |
| `/help` | Display command help |
| `exit` or `quit` | Exit the interactive client |

---

## 7. Related File Links
- 📄 [chat_time_weather_agent_client.py](./chat_time_weather_agent_client.py): Source code for the interactive client
- 📄 [chat_time_weather_agent/agent.py](./chat_time_weather_agent/agent.py): Backend agent and tool implementations
- 📄 [chat_time_weather_agent/README-EN.md](./chat_time_weather_agent/README-EN.md): Detailed specification for chat_time_weather_agent

