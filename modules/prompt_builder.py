import os
import logging

logger = logging.getLogger(__name__)

class PromptBuilder:
    def __init__(self, debug_mode=True):
        self.debug_mode = debug_mode

    def build(self, user_query, search_results, shop_name="General Shop", score_threshold=0.32):
        # 🛡️ 1. INITIALIZE DEFAULTS (No more UnboundLocalError)
        content = "No details available."
        system_base = f"You are Sellica, AI for {shop_name}. You are a helpful shop assistant. If the user speaks Uzbek, reply in clear, simple Uzbek. Do not use English words unless they are product names. If you don't know the answer in Uzbek, say: 'Hozircha buni bilmayman, lekin managerga xabar berdim' (I don't know this yet, but I've informed the manager)."
        relevant_blocks = []

        try:
            # 2. LANGUAGE DETECTION
            uz_keywords = ['bor', 'nima', 'qancha', 'nech', 'salom', 'mi', 'uchun']
            is_uzbek = any(word in user_query.lower() for word in uz_keywords)

            # 3. CONTEXT ASSEMBLY
            for res in search_results:
                try:
                    score = res.get('score', 0)
                    if score >= score_threshold:
                        # Select language-specific content
                        if is_uzbek:
                            current_item_text = res.get('context_uz', 'Ma\'lumot yo\'q')
                        else:
                            current_item_text = res.get('search_en', 'No description')
                        
                        price = res.get('price', 'N/A')
                        block = f"Item: {current_item_text} | Price: {price}"
                        relevant_blocks.append(block)
                except Exception as item_err:
                    logger.error(f"Error processing single search result: {item_err}")
                    continue # Keep going even if one item is broken

            # 4. FINAL CONTEXT STRING
            context_str = "\n".join(relevant_blocks) if relevant_blocks else "NO_DATA_FOUND"

            # 5. FINAL COMPACT PROMPT
            final_prompt = f"{system_base}\n\n<ctx>\n{context_str}\n</ctx>\n\nU: {user_query}\nA:"

            if self.debug_mode:
                print(f"\n--- 🛠️ PROMPT GENERATED ---")
                print(final_prompt[:500] + "...") # Print start of prompt
                print("---" * 10)

            return final_prompt.strip()

        except Exception as e:
            logger.error(f"CRITICAL Error in PromptBuilder: {e}")
            # Fallback prompt so the AI doesn't get a null input
            return f"System: Error building context. Please apologize to the user. User: {user_query}"
        
# --- STANDALONE TEST ---
if __name__ == "__main__":
    builder = PromptBuilder()
    mock_results = [
        {"id": "sw_01", "price": "450k", "search_en": "Warm sweater", "context_uz": "Issiq sviter", "score": 0.9},
    ]
    # Now you pass the shop name dynamically!
    print(builder.build("Sviter nech pul?", mock_results, shop_name="Classic Cargo"))