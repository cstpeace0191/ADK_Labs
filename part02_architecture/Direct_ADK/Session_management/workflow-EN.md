# ADK Runner + Session Rewind Architecture & Workflow

## File Overview

[`direct-adk-agent-rewindsession.py`](./direct-adk-agent-rewindsession.py) is a hands-on script demonstrating the **Runner** and **Session Rewind** capabilities provided by the Google Agent Development Kit (ADK).

> **Core Concepts**
> - `Runner` : A general-purpose runner that executes agents with injected session, artifact, and memory services.
> - `Session State (Working Memory)` : A mutable, in-memory state (`dict`) shared between the Agent and its Tools within a single session.
> - `Session Rewind` : The ability to rollback session state to a point prior to a specified `invocation_id`.

---

## Overall Workflow

```
asyncio.run(main())
        |
        +-- [Create Session] runner.session_service.create_session()
        |         State: {}
        |
        +-- [Step 1] call_agent_async("set state color to red")
        |         --> LLM --> set_state_color("red") --> State: {color: "red"}
        |
        +-- [Step 2] call_agent_async("update state color to blue")
        |         --> LLM --> set_state_color("blue") --> State: {color: "blue"}
        |         <-- events_list (contains invocation_id)
        |
        +-- [Step 3] runner.rewind_async(rewind_before_invocation_id=<blue_invoc_id>)
        |         --> Generate Rewind Event & append to session history
        |         --> Restore State: {color: "red"}
        |
        +-- [Step 4] call_agent_async("what is the current state color?")
                  --> LLM --> get_state_color() --> Returns "red"
```

---

## Component Architecture (Mermaid)

```mermaid
flowchart TB
    subgraph Init["Initialization"]
        E[".env"]
        A["color_agent"]
        TOOLS["tools: set_state_color, get_state_color"]
        R["Runner: color_app"]
        SS["InMemorySessionService"]
        AS["InMemoryArtifactService"]
        MS["InMemoryMemoryService"]

        E --> A
        A --> TOOLS
        TOOLS --> R
        SS -->|"Inject"| R
        AS -->|"Inject"| R
        MS -->|"Inject"| R
    end

    subgraph Step0["Session Creation"]
        S["create_session: user01, empty state"]
    end

    subgraph Step1["Step 1: Set red"]
        U1["User: set state color to red"]
        LLM1["LLM: Gemini"]
        T1["set_state_color red"]
        SC1["state.color = red"]

        U1 --> LLM1
        LLM1 --> T1
        T1 --> SC1
    end

    subgraph Step2["Step 2: Update blue"]
        U2["User: update state color to blue"]
        LLM2["LLM: Gemini"]
        T2["set_state_color blue"]
        SC2["state.color = blue"]
        EV["events_list: invocation_id=inv_B"]

        U2 --> LLM2
        LLM2 --> T2
        T2 --> SC2
        SC2 --> EV
    end

    subgraph Step3["Step 3: Session Rewind"]
        RW["rewind_async to inv_B"]
        RE["Create & append RewindEvent"]
        RESTORE["Restore state.color = red"]

        RW --> RE
        RE --> RESTORE
    end

    subgraph Step4["Step 4: Verify Restoration"]
        U3["User: what is the current state color?"]
        LLM3["LLM: Gemini"]
        T3["get_state_color"]
        ANS["Response: red"]

        U3 --> LLM3
        LLM3 --> T3
        T3 --> ANS
    end

    R --> S
    S --> U1
    SC1 --> U2
    EV --> RW
    RESTORE --> U3
```

---

## Sequence Diagram (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant Main as main()
    participant Runner as Runner
    participant SS as InMemorySessionService
    participant LLM as Gemini 3.8 Flash
    participant Tool as Tool set/get_state_color

    Main->>SS: create_session(app_name, user_id)
    SS-->>Main: session id, state={}

    Note over Main,Tool: Step 1 - Set color to red

    Main->>Runner: run_async set state color to red
    Runner->>LLM: prompt + tool_definitions
    LLM-->>Runner: function_call set_state_color red
    Runner->>Tool: set_state_color red tool_context
    Tool->>SS: state color = red
    Tool-->>Runner: State color set to red
    Runner->>LLM: tool_result
    LLM-->>Runner: final_response
    Runner-->>Main: events_list invocation_id=inv_A

    Note over Main,Tool: Step 2 - Update color to blue

    Main->>Runner: run_async update state color to blue
    Runner->>LLM: prompt + tool_definitions
    LLM-->>Runner: function_call set_state_color blue
    Runner->>Tool: set_state_color blue tool_context
    Tool->>SS: state color = blue
    Tool-->>Runner: State color updated to blue
    Runner->>LLM: tool_result
    LLM-->>Runner: final_response
    Runner-->>Main: events_list invocation_id=inv_B

    Note over Main,SS: Step 3 - Rewind (before inv_B)

    Main->>Runner: rewind_async rewind_before_invocation_id=inv_B
    Runner->>SS: append_event RewindEvent
    Note right of SS: Preserves event history<br/>Calculates inverse state delta<br/>state color = red restored
    SS-->>Runner: OK
    Runner-->>Main: void

    Note over Main,Tool: Step 4 - Query color after rewind

    Main->>Runner: run_async what is the current state color
    Runner->>LLM: prompt + tool_definitions state color=red
    LLM-->>Runner: function_call get_state_color
    Runner->>Tool: get_state_color tool_context
    Tool->>SS: state.get color
    SS-->>Tool: red
    Tool-->>Runner: Current state color is red
    Runner->>LLM: tool_result
    LLM-->>Runner: final_response The color is red
    Runner-->>Main: events_list
```

---

## Core Classes & Functions

| Component | Responsibility |
|---|---|
| `Runner` | Agent execution environment. Injects session, artifact, and memory services to drive agent execution and manage sessions. |
| `runner.session_service` | Handles session CRUD operations (`create_session`, `get_session`, `append_event`). |
| `runner.run_async()` | Executes a single conversational turn, returning an asynchronous stream of events. |
| `runner.rewind_async()` | Rolls back session State and Artifacts to a state prior to the specified `invocation_id`. |
| `ToolContext.state` | Interface allowing Tools to read and write the session Working Memory. |
| `Event.invocation_id` | Unique ID assigned to each `run_async()` invocation turn (used as the anchor for Rewind). |
| `call_agent_async()` | Helper wrapper around `run_async()`. Collects events $\rightarrow$ outputs final response $\rightarrow$ returns `events_list`. |

---

## Rewind Operating Mechanics

```
Event History (Chronological Order)
──────────────────────────────────────────────────────
[inv_A] UserMsg: "set color to red"
[inv_A] ToolCall: set_state_color("red")
[inv_A] ToolResult: color='red'
[inv_A] FinalResponse: "Color set to red."
──────────────────────────────────────────────────────
[inv_B] UserMsg: "update color to blue"
[inv_B] ToolCall: set_state_color("blue")
[inv_B] ToolResult: color='blue'
[inv_B] FinalResponse: "Color updated to blue."
──────────────────────────────────────────────────────
[rewind] RewindEvent(rewind_before_invocation_id=inv_B)
         --> Calculates reverse state delta of all events after inv_B
         --> Restores state["color"] to "red"
──────────────────────────────────────────────────────

Note: The historical event logs are NOT physically deleted.
A RewindEvent is appended to the session, and during subsequent
LLM prompt construction, events after inv_B are logically disregarded.
```

---

## Execution Environment & Setup

### 1. Environment Variable Configuration (`.env`)

Configuration for Vertex AI Express Mode and the `gemini-3.8-flash` model:

```env
# Enable Vertex AI Express Mode
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=ssu-agent-vertex-509708

# gemini-3.8-flash is deployed to the global endpoint; global location is required
GOOGLE_CLOUD_LOCATION=global

# Vertex AI Express Mode Authentication Keys
GOOGLE_API_KEY=AQ.Ab8RN6...
GEMINI_API_KEY=AQ.Ab8RN6...
```

> [!NOTE]
> - When invoking `gemini-3.8-flash` via Vertex AI, configure `GOOGLE_CLOUD_LOCATION=global` instead of a specific region (such as `us-central1`) to prevent 404 NOT_FOUND errors.
> - Keys with the `AQ.` prefix are Vertex AI Express Mode authentication keys and require `GOOGLE_GENAI_USE_VERTEXAI=TRUE`.

### 2. Execution Command

```bash
# Sync dependency packages
uv sync

# Run the script
uv run .\direct-adk-agent-rewindsession.py
```

### 3. Actual Execution Console Output

```text
=== [Session Created] ID: 09a486c6-b40a-4ad1-8378-25959862685c ===
Initial Session State: {}

--- [Step 1] Set state color to red ---

[User] set state color to red
[Agent] The state color has been set to 'red'.
>> State Check: {'color': 'red'}

--- [Step 2] Update state color to blue ---

[User] update state color to blue
[Agent] The state color has been changed to 'blue'.
>> State Check: {'color': 'blue'}

[Target Invocation ID]: e-9a9df7b0-8a21-45f1-bd63-b9b1b107cc8e
--- [Step 3] Execute rewind_async (Roll back blue update) ---
>> Session Rewind Completed!
>> Restored State after Rewind (color should be red): {'color': 'red'}

--- [Step 4] Query Agent for Current Color after Rewind ---

[User] what is the current state color?
[Agent] The current state color is 'red'.
```

---

## Comparison: Runner vs InMemoryRunner

### Summary at a Glance

| | `Runner` | `InMemoryRunner` |
|---|---|---|
| **Nature** | General-purpose Production Runner | Lightweight Runner for testing & learning |
| **Service Injection** | Explicitly specified (Required) | Built-in in-memory implementations used automatically |
| **Persistence** | Connectable to external DBs & cloud storage | Data lost upon process termination |
| **Primary Use Cases** | Production, Cloud Run, Vertex AI | Local development, unit tests, lecture labs |

---

### Constructor Signature Comparison

```python
# Runner — Requires explicit injection of services
Runner(
    agent=agent,
    app_name="my_app",
    session_service=session_service,     # Required
    artifact_service=artifact_service,   # Optional
    memory_service=memory_service,       # Optional
)

# InMemoryRunner — No services required; automatically constructed internally
InMemoryRunner(
    agent=agent,
    app_name="my_app",
)
```

### Internal Architecture (`InMemoryRunner` Source)

```python
class InMemoryRunner(Runner):
    def __init__(self, agent, *, app_name=None, ...):
        super().__init__(
            agent=agent,
            app_name=app_name,
            session_service=InMemorySessionService(),    # Automatic
            artifact_service=InMemoryArtifactService(),  # Automatic
            memory_service=InMemoryMemoryService(),      # Automatic
        )
```

> `InMemoryRunner` is a direct **subclass** of `Runner`.
> It inherits all functionality (`run_async`, `rewind_async`, etc.) intact,
> merely automating the service initialization boilerplate.

---

### Architecture Diagram (Mermaid)

```mermaid
flowchart LR
    subgraph A["Runner - Production"]
        direction TB
        R["Runner"]
        R -->|"Explicit Injection"| SVC1["SessionService<br>e.g., VertexAiSessionService<br>e.g., DatabaseSessionService"]
        R -->|"Explicit Injection"| SVC2["ArtifactService<br>e.g., GcsArtifactService"]
        R -->|"Explicit Injection"| SVC3["MemoryService<br>e.g., VertexAiRagMemoryService"]
    end

    subgraph B["InMemoryRunner - Dev / Test"]
        direction TB
        IMR["InMemoryRunner"]
        IMR -->|"Built-in Default"| MEM1["InMemorySessionService"]
        IMR -->|"Built-in Default"| MEM2["InMemoryArtifactService"]
        IMR -->|"Built-in Default"| MEM3["InMemoryMemoryService"]
    end

    IMR -->|"Extends"| R
```

---

### Code Implementation Patterns (Production Runner Pattern)

[`direct-adk-agent-rewindsession.py`](./direct-adk-agent-rewindsession.py) follows the production-standard pattern using **`Runner` + explicit service injection**. The comparison with the legacy `InMemoryRunner` approach is as follows:

```python
# Legacy InMemoryRunner approach (Lightweight wrapper)
from google.adk.runners import InMemoryRunner

runner = InMemoryRunner(agent=agent, app_name="color_app")


# Production-standard Runner approach (Applied in current script)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService

runner = Runner(
    agent=agent,
    app_name="color_app",
    session_service=InMemorySessionService(),
    artifact_service=InMemoryArtifactService(),
    memory_service=InMemoryMemoryService(),
)
```

All **subsequent call invocations** (`run_async`, `rewind_async`, etc.) **remain completely identical**.

---

### Decision Matrix: When to Use Which?

```mermaid
flowchart TD
    Q1{"Is persistent data<br/>storage required?"}
    Q2{"Does it require integration<br/>with Cloud/Database?"}
    USE_IMR["Use InMemoryRunner<br/>Rapid prototyping, testing & labs"]
    USE_R["Use Runner + External Services<br/>Production & Staging environments"]

    Q1 -->|"No"| USE_IMR
    Q1 -->|"Yes"| Q2
    Q2 -->|"Yes"| USE_R
    Q2 -->|"No, Local Dev"| USE_IMR
```

| Scenario | Recommended Approach |
|---|---|
| Lecture labs / Rapid prototyping | `InMemoryRunner` |
| Unit testing (requires session isolation) | `InMemoryRunner` |
| Staging / Production server deployment | `Runner` + External SessionService |
| Vertex AI Agent Engine integration | `Runner` + `VertexAiSessionService` |
| Session persistence in relational/NoSQL DB | `Runner` + Custom SessionService |

