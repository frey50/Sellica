# modules/groq_client.py
import time
from groq import Groq
from config import GROQ_API_KEY, DEBUG_MODE

class GroqClient:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("[ERROR] GROQ_API_KEY is missing in config.py!")
        
        self.client = Groq(api_key=GROQ_API_KEY)
        # Using the Balanced Beast: Llama 3.3 70B
        self.model = "llama-3.3-70b-versatile" 

        if DEBUG_MODE:
            print(f"\n[DEBUG] Groq: Client Live. Engine: {self.model}")

    def generate_response(self, prompt):    
        if DEBUG_MODE:
            print(f"\n[DEBUG] Groq: Sending prompt ({len(prompt)} chars)...")
            start_time = time.time()

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=1024,
                stream=False
            )

            answer = completion.choices[0].message.content
            
            if DEBUG_MODE:
                latency = time.time() - start_time
                usage = completion.usage
                print(f"[DEBUG] Groq: Response received in {latency:.2f}s")
                print(f"[DEBUG] Groq: Tokens used -> Input: {usage.prompt_tokens} | Output: {usage.completion_tokens}")
                
                # --- FIXED DEBUGGER LINE ---
                # We check if 'prompt_tokens_details' exists AND is not None
                details = getattr(usage, 'prompt_tokens_details', None)
                if details and hasattr(details, 'cached_tokens'):
                    print(f"[DEBUG] Groq: Cache Hit: {details.cached_tokens} tokens saved! 💸")
                else:
                    print(f"[DEBUG] Groq: No cache hit (Prompt too small or first run).")

            return answer.strip()

        except Exception as e:
            # This caught the error last time, now it will be clean!
            print(f"\n[ERROR] Groq API fail: {e}")
            return "Kechirasiz, tizimda biroz uzilish bo'ldi. (AI Offline)"

# --- SURGICAL TEST ---
if __name__ == "__main__":
    # Test with a fake "Sandwich" like the one from our Builder
    test_sandwich = """
    You are Sellica, a chill shop assistant. 
    <context>Question: Price | Answer: 50$</context>
    User: How much is it?
    Sellica:"""
    
    print("="*40)
    print("RUNNING GROQ CLIENT TEST...")
    print("="*40)
    
    bot = GroqClient()
    response = bot.generate_response(test_sandwich)
    
    print("\n--- SELLICA'S VOICE ---")
    print(response)
    print("="*40)