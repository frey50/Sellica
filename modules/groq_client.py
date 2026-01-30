import time
import logging
import traceback
from groq import Groq
from config import GROQ_API_KEY, DEBUG_MODE

# 🎯 Link to our central logging system
logger = logging.getLogger("GroqClient")

class GroqClient:
    def __init__(self):
        # 🛡️ Level 1: Key Validation
        if not GROQ_API_KEY:
            logger.critical("❌ [FATAL] GROQ_API_KEY is missing! Engine cannot start.")
            raise ValueError("[ERROR] GROQ_API_KEY is missing in config.py!")
        
        try:
            self.client = Groq(api_key=GROQ_API_KEY)
            self.model = "llama-3.3-70b-versatile" 
            logger.info(f"✅ [INIT] Groq Engine Live: {self.model}")
        except Exception as e:
            logger.error(f"❌ [INIT] Groq Client failed to instantiate: {e}")
            raise

    def generate_response(self, prompt):    
        # 🛡️ Level 2: Input Validation
        if not prompt or len(prompt.strip()) == 0:
            logger.warning("⚠️ [EMPTY_PROMPT] Received an empty prompt. Skipping AI call.")
            return "Yo bruh, the prompt was empty. I need something to work with!"

        if DEBUG_MODE:
            logger.info(f"📡 [DEBUG] Sending prompt to Groq ({len(prompt)} chars)...")
            start_time = time.time()

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=1024,
                stream=False
            )

            # 🛡️ Level 3: Extraction & Null-Check
            if not completion.choices or not completion.choices[0].message.content:
                logger.error("🚨 [EMPTY_RESPONSE] Groq returned a successful status but ZERO content.")
                return "⚠️ AI Error: The engine returned a blank response. Try again, bruh."

            answer = completion.choices[0].message.content.strip()
            
            # 📊 INDUSTRIAL TELEMETRY
            if DEBUG_MODE:
                latency = time.time() - start_time
                usage = completion.usage
                total_tokens = usage.total_tokens
                ratio = (usage.prompt_tokens / total_tokens) * 100 if total_tokens > 0 else 0
                
                print(f"\n{'='*20} TOKEN STATS {'='*20}")
                print(f"📥 Input (Prompt):  {usage.prompt_tokens} tokens")
                print(f"📤 Output (Answer): {usage.completion_tokens} tokens")
                print(f"⚖️ Prompt Ratio:   {ratio:.1f}%")
                print(f"⏱️ Speed:           {usage.completion_tokens / latency:.1f} tokens/sec")
                print(f"{'='*53}\n")
                    
            return answer

        except Exception as e:
            # 🛡️ Level 4: The "Cold" Traceback
            # This captures if it's a Rate Limit, Auth Error, or Connection Issue
            error_details = traceback.format_exc()
            logger.error(f"💥 [GROQ_FAIL]: {str(e)}")
            logger.debug(f"📑 FULL TRACEBACK:\n{error_details}")
            
            # Return a useful fallback so Telegram doesn't crash
            return "🚧 AI connection snagged. My brain is a bit foggy—try that again in a second!"

# --- SURGICAL TEST ---
if __name__ == "__main__":
    test_sandwich = "User: Hello! Sellica:"
    print("="*40)
    print("RUNNING GROQ CLIENT TEST...")
    bot = GroqClient()
    response = bot.generate_response(test_sandwich)
    print(f"\n--- SELLICA'S VOICE ---\n{response}\n" + "="*40)