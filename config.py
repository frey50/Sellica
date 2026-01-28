import os
from pathlib import Path
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

print("🚀 Loading Sellica Configuration...")

# === 🎯 THE MASTER MAP (Pathlib Style) ===
# This finds the directory where config.py lives.
# On Mac: /Users/frey/Sellica/
# On Railway: /app/
BASE_DIR = Path(__file__).resolve().parent

# === 📂 DYNAMIC FOLDERS ===
DATA_DIR = BASE_DIR / "data"
TEMP_VAULT = BASE_DIR / "temp_vault"

# Ensure folders exist (parents=True handles nested folders)
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMP_VAULT.mkdir(parents=True, exist_ok=True)

# === 📝 FILES ===
# Use .as_posix() if a library specifically requires a string path
USER_REGISTRY = (DATA_DIR / "user_registry.json").as_posix()

# === 🔑 API KEYS ===
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# === 🛡️ TITANIUM GUARD SETTINGS ===
MSG_PER_SESSION = int(os.getenv("MSG_PER_SESSION", "10"))
SESSIONS_PER_PACK = int(os.getenv("SESSIONS_PER_PACK", "2"))
RECHARGE_SECONDS = int(os.getenv("RECHARGE_SECONDS", "3600"))
MIN_MSG_LEN = int(os.getenv("MIN_MSG_LEN", "5"))

# === ⚙️ SYSTEM SETTINGS ===
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "4000"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
BOT_NAME = os.getenv("BOT_NAME", "Sellica")

# === ⚠️ VALIDATION ===
missing_keys = [k for k in ["GROQ_API_KEY", "TELEGRAM_TOKEN", "GITHUB_TOKEN"] if not os.getenv(k)]

if missing_keys:
    print(f"🚨 CRITICAL: Missing keys: {', '.join(missing_keys)}")
else:
    print("✅ All API KEYS loaded successfully")

print(f"📍 Base Path: {BASE_DIR}")
print(f"--- Titanium Guard: {MSG_PER_SESSION} msgs/session | {RECHARGE_SECONDS}s recharge ---")

EMBEDDING_MODEL = "text-embedding-004"