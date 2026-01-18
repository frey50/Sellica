import os
from dotenv import load_dotenv

#soo we are gonna load the .env file okay
load_dotenv()

print("Loading Configuration...")

#=== API KEYS ===
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# === API SETTINGS ===
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "4000"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
BOT_NAME = os.getenv("BOT_NAME", "Sellica")

# === Validation ===
missing_keys = []

if not GROQ_API_KEY:
    missing_keys.append("GROQ_API_KEY")

if not TELEGRAM_TOKEN:
    missing_keys.append("TELEGRAM_TOKEN")
if not GITHUB_TOKEN:
    missing_keys.append("GITHUB_TOKEN")

#show what was loaded
if missing_keys:
    print(f"Mising keys {', '.join(missing_keys)}")
    print(f"")

else:
    print("All API KEYS are loaded")


print(f"   Environment: {ENVIRONMENT}")
print(f"   Debug mode: {DEBUG_MODE}")
print(f"   Max context: {MAX_CONTEXT_LENGTH}")
print(f"   Bot name: {BOT_NAME}")
print()