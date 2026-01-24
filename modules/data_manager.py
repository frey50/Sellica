import os
import time
import shutil
import asyncio
import logging
import json
from modules.github_loader import load_docs
from modules.vectorizer import DocumentVectorizer
from modules.search import DocumentSearch

# Setup Logging for Industry-Level Debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DataManager")

class DataManager:
    def __init__(self, vault_dir="temp_vault"):
        self.vault_dir = vault_dir
        self.registry = {} # { shop_id: {"searcher": obj, "time": float, "in_use": bool} }
        self.vectorizer = DocumentVectorizer()
        self.locks = {} # { shop_id: asyncio.Lock } - One lock per shop
        
        if not os.path.exists(vault_dir):
            os.makedirs(vault_dir)

    def _get_lock(self, shop_id):
        """Ensure only one person builds/modifies a specific shop at a time."""
        if shop_id not in self.locks:
            self.locks[shop_id] = asyncio.Lock()
        return self.locks[shop_id]

    async def get_searcher(self, shop_id):
        """The Main Entry Point: Safe, Locked, and Non-Blocking."""
        lock = self._get_lock(shop_id)
        
        async with lock: # 🛡️ RACE CONDITION SHIELD
            # 1. Check RAM (Fastest)
            if shop_id in self.registry:
                logger.info(f"🚀 [RAM HIT] Serving {shop_id}")
                self.registry[shop_id]["time"] = time.time()
                self.registry[shop_id]["in_use"] = True
                return self.registry[shop_id]["searcher"]

            # 2. Check Disk
            shop_path = os.path.join(self.vault_dir, shop_id)
            vector_file = os.path.join(shop_path, "vectors.jsonl")
            
            if os.path.exists(vector_file):
                logger.info(f"📀 [DISK HIT] Loading {shop_id} into RAM")
                return self._load_to_registry(shop_id, vector_file)

            # 3. Build from Scratch (GitHub -> Vectorize)
            return await self._build_from_scratch(shop_id, shop_path, vector_file)

    async def _build_from_scratch(self, shop_id, shop_path, vector_file):
        logger.info(f"📡 [SYNC] Pulling {shop_id} from GitHub...")
        os.makedirs(shop_path, exist_ok=True)
        
        # 1. Load raw docs
        raw_docs = load_docs(shop_id)
        if not raw_docs:
            logger.error(f"❌ [DATA ERROR] Shop '{shop_id}' not found on GitHub.")
            return None

        # 2. SANITIZE: Filter out 'toxic' data before vectorizing
        clean_docs = [d for d in raw_docs if self._is_valid(d)]
        logger.info(f"🧹 [CLEAN] Kept {len(clean_docs)}/{len(raw_docs)} valid products.")

        # 3. THREAD SHIELD: Run heavy math in a separate thread so the bot doesn't lag
        logger.info(f"🧠 [VECTORS] Initializing vectorization for {shop_id}...")
        try:
            await asyncio.to_thread(self.vectorizer.vectorize_documents, clean_docs, vector_file)
        except Exception as e:
            logger.critical(f"💥 [CRASH] Vectorization failed for {shop_id}: {e}")
            return None

        return self._load_to_registry(shop_id, vector_file)

    def _is_valid(self, doc):
        """Schema Enforcement: The 'Bouncer' at the door."""
        required = ['search_en', 'context_uz']
        return all(key in doc and doc[key] for key in required)

    def _load_to_registry(self, shop_id, vector_file):
        try:
            searcher = DocumentSearch(vector_file)
            self.registry[shop_id] = {
                "searcher": searcher,
                "time": time.time(),
                "in_use": False 
            }
            return searcher
        except Exception as e:
            logger.error(f"❌ [IO ERROR] Failed to load searcher for {shop_id}: {e}")
            return None

  