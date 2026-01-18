# modules/prompt_builder.py

# modules/prompt_builder.py

class PromptBuilder:
    def __init__(self, shop_name="Techwear Shop"):
        self.shop_name = shop_name
        # The 'Soul' of Sellica - Upgraded to be metadata-aware
        self.system_base = (
            f"You are Sellica, the expert AI assistant for {self.shop_name}. "
            "Tone: Professional, relaxed, and helpful. "
            "RULES:\n"
            "1. Answer ONLY using the provided <context>.\n"
            "2. If the user asks for a price, you MUST quote the PRICE from the context.\n"
            "3. If no relevant info is in context, politely say you don't have that detail yet.\n"
            "4. Language: Always reply in the same language the user uses (Uzbek, English, or Russian)."
        )

    def build(self, user_query, search_results, score_threshold=0.38): # Lowered threshold
        print(f"\n[DEBUG] Builder: Processing {len(search_results)} search results...")

        # 1. Filter and Format Rich Context
        relevant_blocks = []
        for res in search_results:
            if res.get('score', 0) >= score_threshold:
                # We build a 'Data Block' so the AI sees the structure clearly
                block = (
                    f"--- ITEM [{res.get('type', 'product').upper()}] ---\n"
                    f"ID: {res.get('id', 'N/A')}\n"
                    f"Price: {res.get('price', 'N/A')}\n"
                    f"English: {res.get('search_en', '')}\n"
                    f"Uzbek: {res.get('context_uz', '')}\n"
                )
                relevant_blocks.append(block)
        
        context_str = "\n".join(relevant_blocks) if relevant_blocks else "NO_RELEVANT_DATA_FOUND"
        
        print(f"[DEBUG] Builder: Injected {len(relevant_blocks)} docs above {score_threshold} threshold.")

        # 2. Construct the Final String (The 'Industrial' Sandwich)
        final_prompt = f"""
{self.system_base}

<context>
{context_str}
</context>

User Question: {user_query}

Sellica's Response:
"""
        return final_prompt.strip()

# --- STANDALONE TEST ---
if __name__ == "__main__":
    builder = PromptBuilder()
    
    # Mock data to test the logic
    mock_results = [
        {"search_en": "Delivery time", "context_uz": "2 kun ichida", "score": 0.95},
        {"search_en": "Wrong item", "context_uz": "O'yinchoq emas", "score": 0.12} # Should be filtered out
    ]
    
    test_query = "Dostavka qancha vaqt?"
    result_prompt = builder.build(test_query, mock_results)
    
    print("\n" + "="*50)
    print("FINAL PROMPT PREVIEW:")
    print("="*50)
    print(result_prompt)