import asyncio
from google.adk.agents import Agent
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

agent = Agent(
    model="gemini-2.5-flash",
    name="event_demo_agent",
    instruction="You are a helpful assistant.",
)

session_service = InMemorySessionService()
runner = Runner(agent=agent, app_name="event_app", session_service=session_service)

async def process_with_events(message: str):
    """Process a message and handle all event types using ADK methods."""
    content = types.Content(role="user", parts=[types.Part(text=message)])

    print(f"\nUser: {message}")
    print(f"{'=' * 50}")

    async for event in runner.run_async(
        user_id="user_1",
        session_id="session_1",
        new_message=content
    ):
        # Print event metadata
        print(f"\n[Event] Author: {event.author}, ID: {event.id}")

        # Check for function calls (tool requests)
        function_calls = event.get_function_calls()
        if function_calls:
            for call in function_calls:
                print(f"  → Tool Call: {call.name}")
                print(f"    Arguments: {call.args}")

        # Check for function responses (tool results)
        function_responses = event.get_function_responses()
        if function_responses:
            for response in function_responses:
                print(f"  ← Tool Result: {response.name}")
                print(f"    Response: {response.response}")

        # Check for text content
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    streaming_status = "[Streaming...]" if event.partial else "[Complete]"
                    print(f"  {streaming_status} {part.text[:100]}...")

        # Check for state changes
        if event.actions and event.actions.state_delta:
            print(f"  State Updated: {event.actions.state_delta}")

        # Check if this is a final response for display
        if event.is_final_response():
            print(f"  ✓ This is a final response")

    print(f"\n{'=' * 50}")

async def main():
    await process_with_events("What is 2 + 2?")

if __name__ == "__main__":
    asyncio.run(main())