import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, filters

# Import our custom modules
from modules.github_loader import list_remote_shops
from modules.data_manager import DataManager 
from modules.groq_client import GroqClient
from modules.prompt_builder import PromptBuilder

# 1. SWISS WATCH LOGGING
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class SellicaBot:
    def __init__(self):
        self.manager = DataManager() 
        self.ai = GroqClient()
        self.prompt_engine = PromptBuilder()

    # 🛡️ THE SAFETY NET: Global Error Handler
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
        if isinstance(update, Update) and update.effective_message:
            # Inform user without crashing
            await update.effective_message.reply_text("😵 I hit a snag. Try again in a second, bruh!")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):   
        try:
            # 🚀 1. DYNAMIC DISCOVERY
            available_shops = list_remote_shops()
            logger.info(f"DEBUG: Scanned shops found: {available_shops}")
            
            if not available_shops:
                await update.message.reply_text("❌ No shop portals found. Check GitHub repo folder 'Datasets'.")
                return
        
            # 🚀 2. DEEP LINK CHECK (e.g., t.me/bot?start=Classic_cargo)
            if context.args:
                shop_id = context.args[0]
                if shop_id in available_shops:
                    await self.manager.get_searcher(shop_id)
                    context.user_data['current_shop'] = shop_id
                    await update.message.reply_text(f"✅ Connected to {shop_id.replace('_', ' ')}!\nAsk me anything.")
                    return
                else:
                    await update.message.reply_text(f"⚠️ Shop '{shop_id}' not found. Choose from the list below:")

            # 🚀 3. KEYBOARD BUILDER (Clean & Optimized)
            keyboard = []
            for s in available_shops:
                # 'slct:' prefix keeps callback_data under the 64-byte Telegram limit
                keyboard.append([InlineKeyboardButton(f"🏪 {s.replace('_', ' ')}", callback_data=f"slct:{s}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "👋 Welcome to Sellica!\nSelect a shop to begin browsing:", 
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"FATAL in start_command: {e}")
            await update.message.reply_text("⚠️ Failed to load shop list. Check logs.")

    async def shop_button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer() # Removes the "loading" circle on the button
        
        try:
            # Extract shop_id from 'slct:shop_name'
            shop_id = query.data.split(":")[1]
            await query.edit_message_text(text=f"⚙️ Powering up {shop_id.replace('_', ' ')}...")
            
            # Load Data into Searcher
            await self.manager.get_searcher(shop_id)
            context.user_data['current_shop'] = shop_id
            
            await query.edit_message_text(text=f"✅ Portal Active: {shop_id.replace('_', ' ')}\nI'm ready. What are you looking for?")
        except Exception as e:
            logger.error(f"Callback error: {e}")
            await query.edit_message_text(text="❌ Error loading shop data. Try /start again.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_text = update.message.text
        shop_id = context.user_data.get('current_shop')
        
        # 🛡️ Guard: Ensure shop is selected
        if not shop_id:
            await update.message.reply_text("Please select a shop first! 🏪 Use /start to see the list.")
            return

        try:
            # Get existing searcher from manager
            searcher = await self.manager.get_searcher(shop_id)
            
            # 1. Perform Semantic Search
            results = searcher.search(user_text, top_k=3)
            
            # 2. Build RAG Prompt
            full_prompt = self.prompt_engine.build(
                user_text, 
                results, 
                shop_name=shop_id.replace('_', ' ')
            )
            
            # 3. Get AI Response
            response = self.ai.generate_response(full_prompt)
            
            if not response:
                response = "I'm having trouble thinking right now. Could you rephrase that?"
                
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            await update.message.reply_text("⚠️ Connection flicker! Let's try that again.")

if __name__ == '__main__':
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TOKEN:
        logger.error("FATAL: No TELEGRAM_TOKEN found in Environment Variables!")
        exit()

    sellica = SellicaBot()
    # Using ApplicationBuilder (Standard for v20+)
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Register Global Error Handler
    app.add_error_handler(sellica.error_handler)
    
    # Handlers (Order matters: Commands first, then Callbacks, then Text)
    app.add_handler(CommandHandler("start", sellica.start_command))
    app.add_handler(CallbackQueryHandler(sellica.shop_button_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), sellica.handle_message))
    
    logger.info("🚀 Sellica Engine is LIVE.")
    app.run_polling()