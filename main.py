import os
import sys
from modules.telegram_bot import SellicaBot # Assuming you saved your class here
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import TELEGRAM_TOKEN, DEBUG_MODE

def main():
    print("="*50)
    print("🚀 SELLICA AI: MULTI-SHOP PORTAL")
    print("="*50)

    # 1. Safety Check: Is the token there?
    if not TELEGRAM_TOKEN:
        print("\n[ERROR] TELEGRAM_TOKEN not found in environment!")
        return

    # 2. Initialize the "Brain" (The Class you just wrote)
    try:
        print("[System] Initializing Sellica Engine...")
        sellica = SellicaBot()
        print("[System] ✅ Engine Loaded. Connecting to Telegram...")
    except Exception as e:
        print(f"\n[ERROR] Initialization failed: {e}")
        return

    # 3. Build the Telegram Application
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # 4. Wire up the Handlers
    # We point these to the methods inside your 'sellica' instance
    app.add_handler(CommandHandler("start", sellica.start_command))
    app.add_handler(CallbackQueryHandler(sellica.shop_button_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), sellica.handle_message))

    # 5. Launch
    print("\n🚀 Sellica is live and secure! Talk to her on Telegram.")
    print("-" * 50)
    
    app.run_polling()

if __name__ == "__main__":
    main()