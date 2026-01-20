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
                total_tokens = usage.total_tokens
                
                # Industrial Efficiency Calculation
                # Let's see if the prompt is taking up more than 80% of our tokens
                ratio = (usage.prompt_tokens / total_tokens) * 100 if total_tokens > 0 else 0
                
                print(f"\n{'='*20} TOKEN STATS {'='*20}")
                print(f"📥 Input (Prompt):  {usage.prompt_tokens} tokens")
                print(f"📤 Output (Answer): {usage.completion_tokens} tokens")
                print(f"⚖️ Prompt Ratio:   {ratio:.1f}%")
                print(f"⏱️ Speed:           {usage.completion_tokens / latency:.1f} tokens/sec")
                print(f"{'='*53}\n")
                    
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