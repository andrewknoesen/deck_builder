# from functools import lru_cache

from google.genai import Client, types

from app.ai.tools.rules import query_comprehensive_rules, lookup_glossary_term
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
3. If a specific keyword or term is unclear, use 'lookup_glossary_term' to find its definition.
4. Answer strictly based on the provided context (Rules and Rulings).
5. Cite rule numbers (e.g., "[CR 702.1]") in your explanation.
6. If the user asks about deck building or strategy, politely decline and say you only focus on rules.

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

        # Map function names to callables
        tool_map = {
            "query_comprehensive_rules": query_comprehensive_rules,
            "lookup_card_rulings": lookup_card_rulings,
            "lookup_glossary_term": lookup_glossary_term,
        }
        
        # Configure the chat session with tools
        chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=self._get_system_instruction(),
                tools=list(tool_map.values()), 
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True), # We handle it manually for control/logging or if SDK auto-handling is tricky
            ),
        )

        full_message = user_message
        if context_cards:
            full_message += f"\n(Context Cards: {', '.join(context_cards)})"

        try:
            logger.info(f"Sending message to model {self.model_name}")
            response = chat.send_message(full_message)

            # Tool execution loop
            max_turns = 20
            for _ in range(max_turns):
                # If there are no function calls, return the text
                if not response.function_calls:
                    if response.text:
                        return response.text
                    else:
                        return "I'm not sure how to answer that."

                # Verify if we have parts to process
                if not response.candidates or not response.candidates[0].content.parts:
                     break

                # Execute all function calls in the response
                function_responses = []
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        fc = part.function_call
                        func_name = fc.name
                        func_args = fc.args
                        
                        logger.info(f"Agent requesting tool execution: {func_name}({func_args})")
                        
                        if func_name in tool_map:
                            try:
                                # Call the tool
                                result = tool_map[func_name](**func_args)
                                logger.info(f"Tool {func_name} output: {str(result)[:100]}...")
                            except Exception as e:
                                logger.error(f"Tool {func_name} failed: {e}")
                                result = f"Error executing tool: {e}"
                        else:
                            result = f"Error: Tool '{func_name}' not found."

                        # Create the function response part
                        function_responses.append(
                            types.Part.from_function_response(
                                name=func_name,
                                response={"result": result}
                            )
                        )

                # Send the tool outputs back to the model
                if function_responses:
                    logger.info(f"Sending {len(function_responses)} tool outputs back to model.")
                    response = chat.send_message(function_responses)
                else:
                    # Should not happen if response.function_calls was true, but safety break
                    break
            
            return "I reached the maximum number of reasoning steps without a final answer."

        except Exception as e:
            logger.error(f"Error during RulesAgent chat: {e}", exc_info=True)
            return "I encountered an error processing your request."


# @lru_cache()
# def get_rules_agent() -> RulesAgent:
#     return RulesAgent()

rules_agent = RulesAgent()
