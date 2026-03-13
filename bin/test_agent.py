import asyncio
import os
import sys

# Ensure backend path is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
sys.path.append(backend_path)

from app.ai.agents.rules import rules_agent

async def main():
    print("Testing RulesAgent with a complex query...")
    query = "How does trample work if the creature also has deathtouch? Cite the rules."
    
    response = await rules_agent.chat(query)
    
    print("\n--- Response ---")
    print(response)
    print("----------------")

if __name__ == "__main__":
    asyncio.run(main())
