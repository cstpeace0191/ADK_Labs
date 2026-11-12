import os
import sys
import asyncio
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from dotenv import load_dotenv

# Ensure UTF-8 output (prevents encoding issues on Windows console)
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv(override=True)

# ── 1. Define Working Memory Tool ──────────────────────────────────
def book_flight(destination: str, tool_context: ToolContext) -> str:
    """Books a flight and saves the result in Working Memory (State)."""
    user_name = tool_context.state.get("user_name", "Customer")
    booking_id = f"BK-{destination.upper()}-1234"

    tool_context.state["current_booking_id"] = booking_id
    tool_context.state["booking_status"] = "CONFIRMED"
    tool_context.state["last_destination"] = destination

    return f"Flight to {destination} has been booked for {user_name}. (Booking ID: {booking_id})"


# ── 2. Configure Agent ──────────────────────────────────────────────
agent = Agent(
    name="flight_agent",
    model="gemini-3.6-flash",
    instruction="""
    You are a travel booking agent.
    Respond kindly, referencing the user's Working Memory (State).
    When a flight booking request is made, always use the book_flight tool.
    """,
    tools=[book_flight],
)

# ── 3. Configure Runner / Session ───────────────────────────────────
APP_NAME = "flight_chat_app"
USER_ID  = "user_001"

session_service = InMemorySessionService()
runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)


# ── Helper: Extract agent response text ─────────────────────────────
async def send_message(session_id: str, user_input: str) -> str:
    """Sends user_input to the agent and returns the final response text."""
    reply = ""
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=types.Content(parts=[types.Part.from_text(text=user_input)]),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            reply = "".join(
                part.text for part in event.content.parts
                if hasattr(part, "text") and part.text
            ).strip()
    return reply


# ── Helper: Print conversation history ──────────────────────────────
async def print_history(session_id: str) -> None:
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session_id
    )
    print("\n" + "=" * 57)
    print("📋  Full Conversation History (session.events)")
    print("=" * 57)
    for event in session.events:
        if not (event.content and event.content.parts):
            continue
        text = "".join(
            part.text for part in event.content.parts
            if hasattr(part, "text") and part.text
        ).strip()
        if not text:
            continue  # Skip tool call / response events
        if event.content.role == "user":
            print(f"  👤 User : {text}")
        else:
            print(f"  🤖 Agent: {text}")
    print("=" * 57)

    print("\n📦 Final Working Memory State:")
    for k, v in session.state.items():
        print(f"   {k}: {v}")
    print()


# ── Main: Chat loop ─────────────────────────────────────────────────
async def main() -> None:
    # Create session + set initial Working Memory
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        state={"user_name": "John Doe", "preferred_airline": "KoreanAir"},
    )
    session_id = session.id

    print("=" * 57)
    print("✈️   Flight Booking Chatbot (Working Memory Demo)")
    print("=" * 57)
    print(f"Session ID   : {session_id}")
    print(f"Initial State: user_name=John Doe, preferred_airline=KoreanAir")
    print("Type 'quit' or 'exit' to terminate\n")

    while True:
        try:
            user_input = input("👤 You  : ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            break

        # Call agent
        reply = await send_message(session_id, user_input)
        print(f"🤖 Agent: {reply}\n")

        # Optionally print modified State summary each turn
        cur = await session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        changed = {k: v for k, v in cur.state.items()
                   if k not in ("user_name", "preferred_airline")}
        if changed:
            print(f"   💾 State Updated: {changed}\n")

    # Print full history upon termination
    await print_history(session_id)
    print("Ending conversation. Thank you! 👋")


if __name__ == "__main__":
    asyncio.run(main())
