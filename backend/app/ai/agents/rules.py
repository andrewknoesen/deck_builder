# from functools import lru_cache

from google.genai import Client, types

from app.ai.tools.rules import query_comprehensive_rules
from app.ai.tools.scryfall import lookup_card_rulings
from app.core.config import settings
from app.core.logging import logger


class RulesAgent:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.model_name = settings.AI_MODEL_NAME
        self.client = None
        if self.api_key:
            self.client = Client(api_key=self.api_key)
        else:
            logger.warning(
                "RulesAgent initialized without API Key. AI features will be disabled."
            )

    def _get_system_instruction(self) -> str:
        return """You are a Level 3 Magic: The Gathering Judge.
Your goal is to answer questions about game rules and card interactions with high precision.

INSTRUCTIONS:
1. ALWAYS verify rules using the 'query_comprehensive_rules' tool. Do not rely on internal memory for specific rule numbers.
2. If specific cards are mentioned, use 'lookup_card_rulings' to check for specific card errata or rulings.
3. Answer strictly based on the provided context (Rules and Rulings).
4. Cite rule numbers (e.g., "[CR 702.1]") in your explanation.
5. If the user asks about deck building or strategy, politely decline and say you only focus on rules.

Format:
**Answer**: [Direct Answer]
**Citations**: [List of Rules/Rulings]
**Explanation**: [Detailed walkthrough]"""

    async def chat(self, user_message: str, context_cards: list[str] = []) -> str:
        logger.info(
            f"RulesAgent received message: '{user_message}' with context_cards: {context_cards}"
        )

        if not self.client:
            logger.error("Attempted to chat but RulesAgent is missing API Key.")
            return "AI Agent not configured (missing API Key)."

        tools = [query_comprehensive_rules, lookup_card_rulings]

        chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=self._get_system_instruction(),
                tools=tools,  # type: ignore
            ),
        )

        full_message = user_message
        if context_cards:
            full_message += f"\n(Context Cards: {', '.join(context_cards)})"

        try:
            logger.info(f"Sending message to model {self.model_name}")
            response = chat.send_message(full_message)

            if response.text:
                logger.info("RulesAgent received valid response from model.")
                return response.text

        except Exception as e:
            logger.error(f"Error during RulesAgent chat: {e}", exc_info=True)
            return "I encountered an error processing your request."

        return "I encountered an error processing your request."


# @lru_cache()
# def get_rules_agent() -> RulesAgent:
#     return RulesAgent()

rules_agent = RulesAgent()
