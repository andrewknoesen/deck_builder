import argparse
import asyncio
import os
import sys

# Ensure we can import from backend/app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.agents.rules.rules_agent import rules_agent
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types


async def main():
    parser = argparse.ArgumentParser(description="Test the MTG Rules Agent")
    parser.add_argument("question", nargs="?", help="The rules question to ask", default="How does Trample work against Protection?")
    args = parser.parse_args()

    print(f"--- Asking Rules Agent ---\nQuestion: {args.question}\n")

    try:
        runner = InMemoryRunner(agent=rules_agent)
        session = await runner.session_service.create_session(
            app_name=runner.app_name, user_id="script-user"
        )
        message = genai_types.Content(
            role="user", parts=[genai_types.Part(text=args.question)]
        )
        response = ""
        async for event in runner.run_async(
            user_id=session.user_id, session_id=session.id, new_message=message
        ):
            if event.is_final_response() and event.content and event.content.parts:
                response = event.content.parts[0].text or ""
        print(f"--- Agent Response ---\n{response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
