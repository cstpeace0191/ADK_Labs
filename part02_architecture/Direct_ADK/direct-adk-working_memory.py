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

# Get API key ('GEMINI_API_KEY' can be obtained for free from Google AI Studio).
API_KEY = os.environ.get('GEMINI_API_KEY')
print(API_KEY)

# 1. Define custom Tool using Working Memory (State)
def book_flight(destination: str, tool_context: ToolContext) -> str:
    # 1-1. Read user info from Working memory (state)
    user_name = tool_context.state.get("user_name", "Customer")
    
    # 1-2. Execute business logic (e.g. flight booking)
    booking_id = f"BK-{destination.upper()}-1234"
    
    # 1-3. Update task progress result to Working memory (state)
    # The next conversation turn or tool can refer to this state
    tool_context.state["current_booking_id"] = booking_id
    tool_context.state["booking_status"] = "CONFIRMED"
    
    return f"Flight to {destination} has been booked for {user_name}. (Booking ID: {booking_id})"

# 2. Configure Agent
agent = Agent(
    name="flight_agent",
    model="gemini-3.6-flash",
    instruction="""
    You are a travel booking agent.
    Respond kindly, referencing the user's state (Working memory).
    """,
    tools=[book_flight]
)

# 3. Configure Session Service (maintains Session and Working memory)
APP_NAME = "flight_app"
USER_ID = "user_001"

session_service = InMemorySessionService()
runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)

async def main():
    # 4. Create session and set Initial Working Memory (State)
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        # Set initial Working Memory
        state={"user_name": "John Doe", "preferred_airline": "KoreanAir"}
    )
    session_id = session.id
    print(f"Session created successfully. ID: {session_id}")

    # 5. Run (session.state and session.events accumulate as conversation progresses)
    user_message = "Please book a flight to Tokyo."
    print(f"\nUser: {user_message}")

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=types.Content(parts=[types.Part.from_text(text=user_message)])
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                text = "".join(
                    part.text for part in event.content.parts
                    if hasattr(part, "text") and part.text
                )
                if text:
                    print(f"Agent: {text}")

    # Check the latest Working Memory (State) of the session
    updated_session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session_id
    )

    # ── Print conversation history ──────────────────────────────────
    print("\n" + "=" * 55)
    print("📋 Conversation History (session.events)")
    print("=" * 55)
    for event in updated_session.events:
        # Extract text parts only
        if not (event.content and event.content.parts):
            continue
        text = "".join(
            part.text for part in event.content.parts
            if hasattr(part, "text") and part.text
        ).strip()
        if not text:
            continue  # Skip tool call / response events

        role = event.content.role  # "user" | "model"
        if role == "user":
            print(f"  👤 User : {text}")
        else:
            print(f"  🤖 Agent: {text}")
    print("=" * 55)

    # Inspect Working Memory (State)
    print("\n📦 Updated Working Memory State:", updated_session.state)
    # Output example: {'user_name': 'John Doe', 'preferred_airline': 'KoreanAir', 'current_booking_id': 'BK-TOKYO-1234', 'booking_status': 'CONFIRMED'}


if __name__ == "__main__":
    asyncio.run(main())
