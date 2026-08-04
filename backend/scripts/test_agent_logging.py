
import sys
import os
import asyncio

# Ensure backend directory is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.ai.agents.rules.rules_agent import rules_agent
from app.core.logging import logger
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

async def main():
    print("\n--- Starting Logging Verification ---\n")

    logger.info("Initializing rules_agent runner for verification...")
    runner = InMemoryRunner(agent=rules_agent)
    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id="script-user"
    )

    # Send a test message
    test_message = "What happens when I declare a blocking creature that is then destroyed?"
    logger.info(f"Sending test message: {test_message}")

    message = genai_types.Content(
        role="user", parts=[genai_types.Part(text=test_message)]
    )
    response = ""
    async for event in runner.run_async(
        user_id=session.user_id, session_id=session.id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response = event.content.parts[0].text or ""

    print(f"\n--- Agent Response ---\n{response}\n")
    print("--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
