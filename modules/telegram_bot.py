import os
import logging
import asyncio
import traceback  # 🔍 Essential for tracing the ghost
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
        self.safety_guard = safety_guard

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_text = update.message.text
        shop_id = context.user_data.get('current_shop')
        
        # 📍 JUNCTION 1: Input Check
        logger.info(f"📥 [INBOUND] User {user_id} | Shop: {shop_id} | Text: '{user_text}'")

        # 1. 🛡️ TIER 1 SAFETY: Access Check
        is_allowed, safety_response = self.safety_guard.check_access(user_id, user_text)
        
        if not is_allowed:
            logger.warning(f"🛡️ [BLOCKED] Safety Guard stopped user {user_id}")
            await update.message.reply_text(safety_response)
            return

        # 2. 🛡️ TIER 2 SAFETY: Context Check
        if not shop_id:
            logger.warning(f"❓ [NO_SHOP] User {user_id} messaged without selecting a shop.")
            await update.message.reply_text("Iltimos, avval do'konni tanlang! 🏪 /start dan foydalaning.")
            return

        try:
            # Mark shop as active
            if shop_id in self.manager.registry:
                self.manager.registry[shop_id]["in_use"] = True
                if self.safety_guard.janitor:
                    self.safety_guard.janitor.touch_shop(shop_id)

            # 📍 JUNCTION 2: RAG Retrieval Check
            searcher = await self.manager.get_searcher(shop_id)
            results = searcher.search(user_text, top_k=3)
            
            # 🕵️‍♂️ Logic Check: Did we find anything?
            logger.info(f"🧐 [DEBUG] RAG found {len(results)} chunks in '{shop_id}'")
            if len(results) == 0:
                logger.warning(f"⚠️ [EMPTY_RAG] No matches found for query: {user_text}")

            # 📍 JUNCTION 3: Prompt & LLM Generation
            full_prompt = self.prompt_engine.build(user_text, results, shop_name=shop_id)
            
            # NOTE: Adding 'await' if your GroqClient is async, keep it as is if sync.
            # We wrap the response in pipes || to see if it's returning whitespace.
            response = self.ai.generate_response(full_prompt)
            logger.info(f"🧠 [DEBUG] RAW AI OUTPUT: |{response}|")

            # 📍 JUNCTION 4: The "Empty Message" Iron Guard
            # This is where we prevent the Telegram crash
            if not response or str(response).strip() == "":
                logger.error("🚨 [CRITICAL] AI returned an empty string! Intercepting crash.")
                response = "⚠️ Ey birodar, AI dvigateli jim. Men manifestni qidirdim, lekin javob yarata olmadim. Qayta ifodalashga harakat qiling!"

            await update.message.reply_text(response)
            logger.info(f"📤 [SUCCESS] Reply sent to user {user_id}")

        except Exception as e:
            # Capture the full crime scene
            error_trace = traceback.format_exc()
            logger.error(f"💥 [PIPELINE CRASH]: {e}\n{error_trace}")
            await update.message.reply_text("😵 Mantiqiy quvurimda xatolikka duch keldim. Qayta urinib ko'ring, birodar!")

        finally:
            if shop_id in self.manager.registry:
                self.manager.registry[shop_id]["in_use"] = False 
                logger.info(f"🔓 [RELEASE] {shop_id} is now idle.")

    # --- Rest of the class remains similar but with added logging ---
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):   
        try:
            user_id = update.effective_user.id
            logger.info(f"🚀 [START] User {user_id} initialized.")
            success, safety_msg = self.safety_guard.refresh_session(user_id)
            
            if not success:
                await update.message.reply_text(safety_msg)
                return

            available_shops = list_remote_shops()
            if not available_shops:
                logger.error("❌ [LOADER] No shops discovered on GitHub.")
                await update.message.reply_text(f"🛡️ {safety_msg}\n\n❌ Do'kon portallari topilmadi.")
                return
        
            keyboard = [[InlineKeyboardButton(f"🏪 {s.replace('_', ' ')}", callback_data=f"slct:{s}")] for s in available_shops]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"🛡️ {safety_msg}\n\n🚀 *Sellica Multi-Shop Portal* faol.\nDo'konni tanlang:",
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"FATAL in start_command: {e}")
            await update.message.reply_text("⚠️ [Tizim xatosi] Portal oflayn.")

    async def shop_button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        try:
            shop_id = query.data.split(":")[1]
            logger.info(f"🔌 [CONNECTING] User selecting shop: {shop_id}")
            await query.edit_message_text(text=f"⚙️ '{shop_id.replace('_', ' ')}' yoqilmoqda...")
            
            await self.manager.get_searcher(shop_id)
            context.user_data['current_shop'] = shop_id

            if self.safety_guard.janitor:
                self.safety_guard.janitor.touch_shop(shop_id)
            
            await query.edit_message_text(text=f"✅ Portal faol: '{shop_id}'\nStok haqida istalgan narsani so'rang!")
        except Exception as e:
            logger.error(f"Callback error: {e}")
            await query.edit_message_text(text="❌ Do'kon ma'lumotlarini yuklashda xatolik.")