import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Import our custom modules
from modules.github_loader import list_remote_shops
from modules.data_manager import DataManager 
from modules.groq_client import GroqClient
from modules.prompt_builder import PromptBuilder

# 1. SWISS WATCH LOGGING
logger = logging.getLogger("SellicaBot")

class SellicaBot:
    def __init__(self, safety_guard):
        self.manager = DataManager() 
        self.ai = GroqClient()
        self.prompt_engine = PromptBuilder()
        # 🛡️ New Security Guard & Janitor Integration
        self.safety_guard = safety_guard

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text("😵 I hit a snag. Try again in a second, bruh!")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):   
        try:
            user_id = update.effective_user.id
            
            # 🛡️ 1. TITANIUM GATE: Session & Quota Check
            success, safety_msg = self.safety_guard.refresh_session(user_id)
            
            if not success:
                await update.message.reply_text(safety_msg)
                return

            # 🚀 2. DYNAMIC DISCOVERY: Fetch Shop List
            available_shops = list_remote_shops()
            
            if not available_shops:
                await update.message.reply_text(f"🛡️ {safety_msg}\n\n❌ No shop portals found. Check GitHub repo.")
                return
        
            # 🚀 3. DEEP LINK CHECK
            if context.args:
                shop_id = context.args[0]
                if shop_id in available_shops:
                    await self.manager.get_searcher(shop_id)
                    context.user_data['current_shop'] = shop_id
                    
                    # 🔥 HEARTBEAT: Keep shop alive on deep-link start
                    if self.safety_guard.janitor:
                        self.safety_guard.janitor.touch_shop(shop_id)

                    await update.message.reply_text(
                        f"🛡️ {safety_msg}\n\n✅ Connected to {shop_id.replace('_', ' ')}!\nAsk me anything."
                    )
                    return

            # 🚀 4. KEYBOARD BUILDER
            keyboard = [[InlineKeyboardButton(f"🏪 {s.replace('_', ' ')}", callback_data=f"slct:{s}")] for s in available_shops]
            reply_markup = InlineKeyboardMarkup(keyboard)

            welcome_text = (
                f"🛡️ {safety_msg}\n\n"
                "🚀 *Sellica Multi-Shop Portal* is active.\n"
                "Please select a shop to begin browsing:"
            )
            
            await update.message.reply_text(
                welcome_text, 
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"FATAL in start_command: {e}")
            await update.message.reply_text("⚠️ [System Error] Portal offline. Try again, bruh.")

    async def shop_button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        try:
            shop_id = query.data.split(":")[1]
            await query.edit_message_text(text=f"⚙️ Powering up {shop_id.replace('_', ' ')}...")
            
            # Initialize searcher
            await self.manager.get_searcher(shop_id)
            context.user_data['current_shop'] = shop_id

            # 🔥 HEARTBEAT: Reset timer as soon as they pick a shop
            if self.safety_guard.janitor:
                self.safety_guard.janitor.touch_shop(shop_id)
            
            await query.edit_message_text(
                text=f"✅ Portal Active: {shop_id.replace('_', ' ')}\nI'm ready. What are you looking for?"
            )
        except Exception as e:
            logger.error(f"Callback error: {e}")
            await query.edit_message_text(text="❌ Error loading shop data.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_text = update.message.text
        shop_id = context.user_data.get('current_shop')

        # 1. 🛡️ TIER 1 SAFETY: Access Check
        is_allowed, safety_response = self.safety_guard.check_access(user_id, user_text)
        
        if not is_allowed:
            await update.message.reply_text(safety_response)
            return

        # 2. 🛡️ TIER 2 SAFETY: Context Check
        if not shop_id:
            await update.message.reply_text("Please select a shop first! 🏪 Use /start.")
            return

        try:
            # 1. MARK AS BUSY
            if shop_id in self.manager.registry:
                self.manager.registry[shop_id]["in_use"] = True
                self.safety_guard.janitor.touch_shop(shop_id)

            # 2. RUN SEARCH & AI
            searcher = await self.manager.get_searcher(shop_id)
            results = searcher.search(user_text, top_k=3)
            full_prompt = self.prompt_engine.build(user_text, results, shop_name=shop_id)
            response = self.ai.generate_response(full_prompt)

            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("Snagged! Try again.")

        finally:
            # 3. 🔓 THE KEY FIX: Release the shop so the Janitor can clean it
            if shop_id in self.manager.registry:
                self.manager.registry[shop_id]["in_use"] = False # <--- THIS RELEASES IT
                logger.info(f"🔓 {shop_id} is now idle and ready for Janitor.")