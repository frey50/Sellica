# main.py
import os
import sys
from modules.search import DocumentSearch as Searcher
from modules.prompt_builder import PromptBuilder
from modules.groq_client import GroqClient
from config import DEBUG_MODE

def main():
    # 1. Path Setup (The Robust Way)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    vector_file = os.path.join(base_dir, "data", "vectors.jsonl")

    print("="*50)
    print("🚀 SELLICA AI: TECHWEAR SHOP ASSISTANT")
    print("="*50)

    # 2. Safety Check: Does the brain exist?
    if not os.path.exists(vector_file):
        print(f"\n[ERROR] Brain not found at {vector_file}")
        print("Please run your ingestion/rebuild script first!")
        return

    # 3. Initialization
    try:
        print("[System] Initializing Modules...")
        searcher = Searcher(vectors_path=vector_file)
        builder = PromptBuilder(shop_name="Techwear Shop")
        ai_voice = GroqClient()
        print("[System] ✅ All systems online. Ready to chat!")
    except Exception as e:
        print(f"\n[ERROR] Startup failed: {e}")
        return

    print("\n(Type 'exit' to quit)")
    print("-" * 50)

    # 4. The Conversation Loop
    while True:
        user_query = input("\n👤 You: ").strip()

        if user_query.lower() in ['exit', 'quit', 'bye']:
            print("\nSellica: Stay fresh, bruh! See ya. ✌️")
            break
        
        if not user_query:
            continue

        # --- THE RAG FLOW ---
        
        # Step A: Search for context
        if DEBUG_MODE: print(f"[DEBUG] Main: Searching memories...")
        # Note: using top_k to match your DocumentSearch class!
        context = searcher.search(user_query, top_k=3)

        # Step B: Build the "Sandwich" Prompt
        if DEBUG_MODE: print(f"[DEBUG] Main: Building prompt...")
        final_prompt = builder.build(user_query, context)

        # Step C: Get the AI's response
        if DEBUG_MODE: print(f"[DEBUG] Main: Sending to Groq...")
        response = ai_voice.generate_response(final_prompt)

        # Step D: Output
        print(f"\n✨ Sellica: {response}")
        print("-" * 30)

if __name__ == "__main__":
    main()