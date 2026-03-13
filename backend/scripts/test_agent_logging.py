
import sys
import os
import asyncio

# Ensure backend directory is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.ai.agents.rules.rules_agent import RulesAgent
from app.core.logging import logger

async def main():
    print("\n--- Starting Logging Verification ---\n")
    
    # Initialize agent
    logger.info("Initializing RulesAgent for verification...")
    agent = RulesAgent()
    
    # Send a test message
    test_message = "What happens when I declare a blocking creature that is then destroyed?"
    logger.info(f"Sending test message: {test_message}")
    
    response = await agent.chat(test_message)
    
    print(f"\n--- Agent Response ---\n{response}\n")
    print("--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
