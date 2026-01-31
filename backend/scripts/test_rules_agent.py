import argparse
import asyncio
import os
import sys

# Ensure we can import from backend/app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.agents import rules_agent


async def main():
    parser = argparse.ArgumentParser(description="Test the MTG Rules Agent")
    parser.add_argument("question", nargs="?", help="The rules question to ask", default="How does Trample work against Protection?")
    args = parser.parse_args()

    print(f"--- Asking Rules Agent ---\nQuestion: {args.question}\n")
    
    try:
        response = await rules_agent.chat(args.question)
        print(f"--- Agent Response ---\n{response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
