import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

print("Loading Configuration...")

# === API KEYS ===
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# === TITANIUM GUARD SETTINGS (DYNAMIC) ===
# We use env vars with defaults so you can change them without touching code
MSG_PER_SESSION = int(os.getenv("MSG_PER_SESSION", "2"))
SESSIONS_PER_PACK = int(os.getenv("SESSIONS_PER_PACK", "2"))
RECHARGE_SECONDS = int(os.getenv("RECHARGE_SECONDS", "20"))
MIN_MSG_LEN = int(os.getenv("MIN_MSG_LEN", "5"))

# === PATHS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMP_VAULT = os.path.join(BASE_DIR, "temp_vault")
USER_REGISTRY = os.path.join(DATA_DIR, "user_registry.json")

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

# Ensure necessary directories exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(TEMP_VAULT):
    os.makedirs(TEMP_VAULT)

# Show what was loaded
if missing_keys:
    print(f"🚨 Missing keys: {', '.join(missing_keys)}")
else:
    print("✅ All API KEYS are loaded")

print(f"   Environment: {ENVIRONMENT}")
print(f"   Debug mode: {DEBUG_MODE}")
print(f"   Max context: {MAX_CONTEXT_LENGTH}")
print(f"   Bot name: {BOT_NAME}")
print(f"--- Titanium Guard ---")
print(f"   Msgs/Session: {MSG_PER_SESSION}")
print(f"   Sessions/Pack: {SESSIONS_PER_PACK}")
print(f"   Recharge: {RECHARGE_SECONDS}s")
print()