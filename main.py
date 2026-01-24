import os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Import our custom modules
from modules.telegram_bot import SellicaBot
from modules.safety_service import SafetyService
from modules.janitor_service import JanitorService
import config  # Central Source of Truth

# ==========================================
# 🔍 PRO-LEVEL LOGGING
# ==========================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
# Keep the logs clean by silencing library noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logger = logging.getLogger("MainEntry")

# 🛡️ GLOBAL SAFETY GUARD: Shared instance for all user limits
# This is initialized once and passed into SellicaBot
safety_guard = SafetyService()

async def start_background_tasks(application):
    """🧹 Starts the Janitor Service with absolute precision."""
    try:
        # Pull the bot engine instance
        sellica = application.bot_data['sellica']
        
        # 🔥 SYNCED VAULT: Use the path from config.py
        vault_dir = config.TEMP_VAULT

        # 🔥 THE TITANIUM WIRING:
        # We pass the Shop Registry and the Safety Guard to the Janitor
        janitor = JanitorService(
            registry=sellica.manager.registry, 
            vault_dir=vault_dir,
            safety_service=safety_guard, 
            interval=5,  # ⚡ FAST PATROL: Every 5s for testing
            ttl=15       # ⚡ FAST WIPE: 15s for testing
        )
        
        # Link janitor to safety_guard so they can talk (Heartbeats)
        safety_guard.janitor = janitor
        
        # Store in bot_data and fire the task
        application.bot_data['janitor'] = janitor
        asyncio.create_task(janitor.start())
        
        logger.info(f"🧹 [SYSTEM] Janitor patrolling: {vault_dir} (Interval: 5s, TTL: 15s)")
        
    except Exception as e:
        logger.error(f"❌ [SYSTEM] Janitor failed to start: {e}")

async def reset_command(update, context):
    """🛠️ GOD MODE: Total wipe for testing."""
    user_id = update.effective_user.id
    uid = str(user_id)
    
    if uid in safety_guard.user_data:
        # Wipes everything: msg count, session count, AND the timer
        del safety_guard.user_data[uid]
        safety_guard._save_data()
        
        # Clear shop selection from Telegram's context memory
        context.user_data.clear() 
        
        await update.message.reply_text("🧹 [DEBUG] Registry & Timer wiped. You are a ghost now. Use /start!")
        logger.info(f"🗑️ [DEBUG] Manual wipe performed for user {uid}")
    else:
        await update.message.reply_text("🤷‍♂️ No registry data found for your ID.")

def main():
    logger.info(f"🚀 {config.BOT_NAME}: System Booting...")

    # 1. Check for critical keys
    if not config.TELEGRAM_TOKEN:
        logger.critical("❌ [FATAL] TELEGRAM_TOKEN is missing from .env or config!")
        return

    # 2. Initialize Bot Engine
    # We pass the shared safety_guard here so the bot can check message limits
    sellica_engine = SellicaBot(safety_guard=safety_guard)

    # 3. Build Application
    app = ApplicationBuilder() \
        .token(config.TELEGRAM_TOKEN) \
        .post_init(start_background_tasks) \
        .build()
    
    # Store engine in bot_data for the Janitor to access
    app.bot_data['sellica'] = sellica_engine

    # 4. HANDLERS (Priority Order)
    # /resetme is first so it always works even if the bot is "stuck"
    app.add_handler(CommandHandler("resetme", reset_command)) 
    app.add_handler(CommandHandler("start", sellica_engine.start_command))
    
    # Handles shop selection buttons
    app.add_handler(CallbackQueryHandler(sellica_engine.shop_button_callback))
    
    # The message handler runs the 'check_access' logic inside sellica_engine.handle_message
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), sellica_engine.handle_message))

    logger.info(f"🚀 [LIVE] {config.BOT_NAME} is fully shielded and online.")
    
    try:
        # drop_pending_updates=True prevents the bot from spamming old messages on restart
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.critical(f"🛑 [CRASH] System failure: {e}")

if __name__ == "__main__":
    main()