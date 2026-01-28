import time
import asyncio
import logging
import gc
import config 
from modules.github_loader import load_docs
from modules.vectorizer import DocumentVectorizer
from modules.search import DocumentSearch

logger = logging.getLogger("DataManager")

class DataManager:
    def __init__(self):
        self.vault_dir = config.TEMP_VAULT
        self.registry = {} 
        # The vectorizer init now handles the 2026 gemini-embedding-001 setup
        self.vectorizer = DocumentVectorizer()
        self.locks = {} 

    def _get_lock(self, shop_id):
        if shop_id not in self.locks:
            self.locks[shop_id] = asyncio.Lock()
        return self.locks[shop_id]

    async def get_searcher(self, shop_id):
        lock = self._get_lock(shop_id)
        
        async with lock:
            # 1. RAM Check
            if shop_id in self.registry:
                # Ensure the searcher actually exists in the dict
                if self.registry[shop_id].get("searcher"):
                    logger.info(f"🚀 [RAM HIT] Serving {shop_id}")
                    self.registry[shop_id]["time"] = time.time()
                    self.registry[shop_id]["in_use"] = True
                    return self.registry[shop_id]["searcher"]

            # 2. Disk Check
            shop_path = self.vault_dir / shop_id
            vector_file = shop_path / "vectors.jsonl"
            
            if vector_file.exists():
                logger.info(f"📀 [DISK HIT] Loading {shop_id} into RAM")
                return self._load_to_registry(shop_id)

            # 3. Build from Scratch (The 2026 Path)
            return await self._build_from_scratch(shop_id, shop_path, vector_file)

    async def _build_from_scratch(self, shop_id, shop_path, vector_file):
        logger.info(f"📡 [SYNC] Pulling {shop_id} from GitHub...")
        shop_path.mkdir(parents=True, exist_ok=True)
        
        raw_docs = load_docs(shop_id)
        if not raw_docs:
            logger.error(f"❌ [DATA ERROR] Shop '{shop_id}' not found on GitHub.")
            return None

        clean_docs = [d for d in raw_docs if self._is_valid(d)]
        
        logger.info(f"🧠 [VECTORS] Vectorizing {len(clean_docs)} items...")
        try:
            # We use to_thread because embedding 100+ items is a blocking CPU/Network task
            # Passing vector_file.as_posix() ensures compatibility with all OS
            await asyncio.to_thread(self.vectorizer.vectorize_documents, clean_docs, vector_file.as_posix())
        except Exception as e:
            logger.critical(f"💥 [CRASH] Vectorization failed for {shop_id}: {e}")
            return None

        return self._load_to_registry(shop_id)

    def _load_to_registry(self, shop_id):
        """Initializes the searcher and protects the registry."""
        try:
            # Attempt to create the searcher
            searcher = DocumentSearch(shop_id) 
            
            # CRITICAL: Check if vectors actually loaded
            if searcher.vectors is None or len(searcher.documents) == 0:
                logger.error(f"⚠️ [EMPTY] {shop_id} searcher initialized but has no vectors.")
                return None

            self.registry[shop_id] = {
                "searcher": searcher,
                "time": time.time(),
                "in_use": False 
            }
            return searcher
        except Exception as e:
            logger.error(f"❌ [IO ERROR] Failed to link searcher for {shop_id}: {e}")
            return None

    def _is_valid(self, doc):
        """Strict validation for product data structure."""
        # Ensure we have the searchable text and the context
        return all(key in doc and str(doc[key]).strip() for key in ['search_en', 'context_uz'])