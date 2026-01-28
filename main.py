import asyncio
import logging
import os
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import Update

# Custom modules
from modules.telegram_bot import SellicaBot
from modules.safety_service import SafetyService
from modules.janitor_service import JanitorService
import config 

# --- LOGGING SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logger = logging.getLogger("MainEntry")

# 🛡️ GLOBAL SAFETY GUARD
safety_guard = SafetyService()

async def start_background_tasks(application):
    """🧹 Starts the Janitor with a safety check on the engine."""
    try:
        # Check if the bot engine actually initialized
        sellica = application.bot_data.get('sellica')
        if not sellica or not hasattr(sellica, 'manager'):
            logger.error("🛑 [SYSTEM] Engine not found. Janitor standing down.")
            return

        j_interval = int(os.getenv("JANITOR_INTERVAL", "30"))
        j_ttl = int(os.getenv("JANITOR_TTL", "900"))

        janitor = JanitorService(
            registry=sellica.manager.registry, 
            safety_service=safety_guard, 
            interval=j_interval,
            ttl=j_ttl
        )
        
        safety_guard.janitor = janitor
        application.bot_data['janitor'] = janitor
        asyncio.create_task(janitor.start())
        
        logger.info(f"🧹 [SYSTEM] Janitor patrolling: {config.TEMP_VAULT} (Interval: {j_interval}s)")
        
    except Exception as e:
        logger.error(f"❌ [SYSTEM] Janitor failed: {e}")

async def error_handler(update: object, context):
    """📡 SYSTEM WATCHDOG: Catches API timeouts and crashes."""
    logger.error(f"⚠️ [CRASH] Update {update} caused error: {context.error}")
    # Optional: Send a 'System Busy' message to the user if update is a Message
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("🚧 System is a bit overloaded. Give me a second!")

async def reset_command(update, context):
    """🛠️ GOD MODE: Total wipe for testing."""
    uid = str(update.effective_user.id)
    if uid in safety_guard.user_data:
        del safety_guard.user_data[uid]
        safety_guard._save_data()
        context.user_data.clear() 
        await update.message.reply_text("🧹 [DEBUG] Registry & Timer wiped. Go again!")
    else:
        await update.message.reply_text("🤷‍♂️ Nothing to wipe.")

def main():
    logger.info(f"🚀 {config.BOT_NAME}: System Booting...")

    # 1. Initialize Bot Engine
    try:
        sellica_engine = SellicaBot(safety_guard=safety_guard)
    except Exception as e:
        logger.critical(f"❌ [FATAL] Engine failed to start: {e}")
        return

    # 2. Build Application
    app = ApplicationBuilder() \
        .token(config.TELEGRAM_TOKEN) \
        .post_init(start_background_tasks) \
        .build()
    
    app.bot_data['sellica'] = sellica_engine

    # 3. GLOBAL ERROR CATCHER
    app.add_error_handler(error_handler)

    # 4. HANDLERS
    app.add_handler(CommandHandler("resetme", reset_command)) 
    app.add_handler(CommandHandler("start", sellica_engine.start_command))
    app.add_handler(CallbackQueryHandler(sellica_engine.shop_button_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), sellica_engine.handle_message))

    logger.info(f"🚀 [LIVE] {config.BOT_NAME} online.")
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()