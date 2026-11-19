# direct-adk-fastapi-server — Operational Architecture & Workflow Guide

This document details the operational architecture and workflow of [`direct-adk-fastapi-server.py`](./direct-adk-fastapi-server.py), which packages Google Agent Development Kit's (ADK) `LlmAgent` and `Runner` into a high-performance asynchronous REST API microservice using FastAPI.

---

## 1. Overview & Core Concepts

[`direct-adk-fastapi-server.py`](./direct-adk-fastapi-server.py) transitions an ADK agent from a standalone command-line script into a production-ready HTTP microservice. It exposes endpoints that allow web applications, mobile frontends, and terminal clients to engage in multi-turn conversations and trigger live tools (weather reports, local times) via standard HTTP requests.

> **Key Components**
> - **`FastAPI` Web Framework**: Provides asynchronous request handling (Async/Await), automatic OpenAPI (Swagger) documentation, and Pydantic-based input validation.
> - **`LlmAgent (weather_and_time_agent)`**: An agent powered by `gemini-3.8-flash` equipped with natural language instructions and two dedicated tools (`get_weather`, `get_current_time`).
> - **`Runner` & `InMemorySessionService`**: The ADK runtime engine that manages session lifecycles, event history tracking (`events`), and asynchronous event dispatching (`run_async`).

---

## 2. System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Client Layer"]
        CLI["direct-adk-fastapi-client.py"]
        WEB["Web Frontends / Mobile Apps"]
        CURL["cURL / HTTP Clients"]
    end

    subgraph FastAPILayer["FastAPI Microservice Layer (direct-adk-fastapi-server.py)"]
        direction TB
        ROUTER["API Router<br>(/health, /sessions, /chat)"]
        VALID["Pydantic Schema Validation<br>(ChatRequest, SessionCreateRequest)"]
        SESS_MGR["Session Manager Function<br>(get_or_create_session)"]
        ROUTER --> VALID --> SESS_MGR
    end

    subgraph ADKLayer["ADK Runtime Layer"]
        direction TB
        RUNNER["ADK Runner (weather_time_fastapi_app)"]
        SESS_SVC["InMemorySessionService<br>(Session State & Event History)"]
        AGENT["LlmAgent (weather_and_time_agent)<br>Model: gemini-3.8-flash"]
        RUNNER <--> SESS_SVC
        RUNNER <--> AGENT
    end

    subgraph ToolLayer["Tools & External Services Layer"]
        direction TB
        GEO["_geocode (Open-Meteo Geocoding)"]
        W_TOOL["get_weather (Open-Meteo Forecast)"]
        T_TOOL["get_current_time (ZoneInfo Local Time)"]
        LLM_SVC["Google Gemini API (Vertex AI)"]
        AGENT --> LLM_SVC
        AGENT --> W_TOOL
        AGENT --> T_TOOL
        W_TOOL --> GEO
        T_TOOL --> GEO
    end

    ClientLayer ==>|HTTP JSON Request| ROUTER
    SESS_MGR ==>|Async Execution| RUNNER
```

---

## 3. Conversation Processing Lifecycle (Sequence Diagram)

The following diagram illustrates how the server processes a conversation turn when a client calls `/chat`:

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client
    participant API as FastAPI Router (/chat)
    participant SM as get_or_create_session
    participant SS as InMemorySessionService
    participant Runner as ADK Runner
    participant Agent as LlmAgent
    participant LLM as Gemini API
    participant Tool as Weather/Time Tools

    Client->>API: POST /chat (message="Weather in Seoul?", session_id=None, user_id="user01")
    API->>SM: get_or_create_session(session_id=None, user_id="user01")
    SM->>SS: create_session(sid="session_a1b2c3d4")
    SS-->>SM: Session initialized
    SM-->>API: session_id = "session_a1b2c3d4"

    API->>Runner: runner.run_async(user_id, session_id, new_message)
    Runner->>SS: Load prior session events (Context Injection)
    Runner->>Agent: Dispatch message & historical events

    Agent->>LLM: Evaluate user prompt & determine tool execution
    LLM-->>Agent: FunctionCall(name="get_weather", args={"city": "Seoul"})
    Agent->>Tool: Execute get_weather("Seoul")
    Tool-->>Agent: {"status": "success", "report": "Weather in Seoul: Clear..."}
    Agent->>LLM: Forward tool results & request final answer synthesis
    LLM-->>Agent: Return synthesized final answer

    Agent-->>Runner: Event(is_final_response=True, content="Current weather in Seoul is...")
    Runner->>SS: Record emitted events into session store
    Runner-->>API: Extract final response text
    API-->>Client: 200 OK ChatResponse(response="Current weather in Seoul is...", session_id="session_a1b2c3d4")
```

---

## 4. Key Endpoints & Implementation Logic

### 1) Health Check (`GET /health`)
Returns the operational status, app identifier, and active LLM model of the underlying ADK agent.
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": APP_NAME,
        "agent": agent.name,
        "model": agent.model,
    }
```

### 2) Explicit Session Creation (`POST /sessions`)
Allows clients to explicitly pre-allocate a session ID before initiating conversation.
* **Request**: `SessionCreateRequest(user_id="user01")`
* **Response**: `SessionCreateResponse(session_id="session_xxx", user_id="user01", status="created")`

### 3) Session Inspection (`GET /sessions/{session_id}`)
Retrieves session metadata, including the cumulative event count (`event_count`) and state variables (`state`), for debugging and telemetry.

### 4) Conversation Turn (`POST /chat`)
Consumes the ADK Runner's asynchronous generator to process user queries into agent responses:
```python
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    user_id = req.user_id or DEFAULT_USER_ID
    session_id = await get_or_create_session(req.session_id, user_id)

    content = types.Content(role="user", parts=[types.Part(text=req.message)])
    response_text = ""

    # Consume the ADK asynchronous event generator
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                texts = [p.text for p in event.content.parts if hasattr(p, "text") and p.text]
                if texts:
                    response_text = "\n".join(texts).strip()

    return ChatResponse(response=response_text or "(No response)", session_id=session_id)
```

---

## 5. Execution & Verification Guide

### 1) Start the Server
Launch the server using `uv run` or standard `python`:
```bash
# Execute from part02_architecture directory
uv run Direct_ADK/direct-adk-fastapi-server.py
```
Upon startup, the console displays:
```text
=================================================================
  🚀 Starting ADK Agent FastAPI Server on http://127.0.0.1:8000
=================================================================
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 2) Swagger UI API Documentation
Open `http://127.0.0.1:8000/docs` in your web browser to access the auto-generated Swagger UI and test endpoints directly.

### 3) Quick Testing via cURL
```bash
# 1. Health check
curl -X GET http://127.0.0.1:8000/health

# 2. Weather query with automatic session creation
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather and local time in Paris?"}'
```

---

## 6. Related File Links
- 📄 [direct-adk-fastapi-server.py](./direct-adk-fastapi-server.py): FastAPI server source code
- 📄 [direct-adk-fastapi-client.py](./direct-adk-fastapi-client.py): Dedicated interactive terminal client source code
- 📄 [direct-adk-fastapi-client-workflow-README-EN.md](./direct-adk-fastapi-client-workflow-README-EN.md): Client operational workflow guide

