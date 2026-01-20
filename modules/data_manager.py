import os
import time
import shutil
import asyncio
from modules.github_loader import load_docs
from modules.vectorizer import DocumentVectorizer
from modules.search import DocumentSearch # Your existing search logic

class DataManager:
    def __init__(self, vault_dir="temp_vault"):
        self.vault_dir = vault_dir
        self.registry = {} # { shop_id: {"searcher": obj, "time": float} }
        self.vectorizer = DocumentVectorizer() # Load model ONCE in init
        
    async def get_searcher(self, shop_id):
        # 1. Check RAM
        if shop_id in self.registry:
            self.registry[shop_id]["time"] = time.time()
            return self.registry[shop_id]["searcher"]

        # 2. Check Disk
        shop_path = os.path.join(self.vault_dir, shop_id)
        vector_file = os.path.join(shop_path, "vectors.jsonl")
        
        if os.path.exists(vector_file):
            return self._load_into_ram(shop_id, vector_file)

        # 3. Pull from Cold Storage (GitHub)
        return await self._build_from_scratch(shop_id, shop_path, vector_file)

    async def _build_from_scratch(self, shop_id, shop_path, vector_file):
            """REAL PULL & VECTORIZE"""
            print(f"📡 [DataManager] Initializing Birth for {shop_id}...")
            os.makedirs(shop_path, exist_ok=True)
            
            # 1. Pull real docs from GitHub
            docs = load_docs(shop_id) 
            if not docs:
                print(f"❌ [DataManager] GitHub folder '{shop_id}' is empty or missing.")
                return None
            
            # 2. Vectorize them (This creates the vectors.jsonl on your Mac)
            print(f"🧠 [DataManager] Vectorizing {len(docs)} documents...")
            self.vectorizer.vectorize_documents(docs, vector_file)
            
            # 3. Initialize the Searcher and put in RAM
            return self._load_to_registry(shop_id, vector_file)

    def _load_to_registry(self, shop_id, vector_file):
        """REAL SEARCHER INITIALIZATION"""
        print(f"🔋 [DataManager] Powering up Searcher for {shop_id}...")
        
        # Create the actual brain object
        searcher = DocumentSearch(vector_file) 
        
        self.registry[shop_id] = {
            "searcher": searcher,
            "time": time.time()
        }
        return searcher

    async def janitor_task(self):
        """
        The background loop that watches for 'dead' shops.
        Set to 60 seconds for our test.
        """
        print("🧹 [Janitor] Service started. Scanning every 10 seconds...")
        
        while True:
            await asyncio.sleep(10) # Check frequently during testing
            now = time.time()
            expired_shops = []

            # Logic: Find who has been silent for too long
            for shop_id, data in self.registry.items():
                time_since_last_use = now - data["time"]
                
                if time_since_last_use > 60: # OUR 1-MINUTE TEST LIMIT
                    expired_shops.append(shop_id)

            # Logic: Kill the expired shops
            for shop_id in expired_shops:
                print(f"🚮 [Janitor] Shop '{shop_id}' has been inactive for 60s. Wiping...")
                
                # 1. Remove from RAM
                del self.registry[shop_id]
                
                # 2. Remove from Disk
                shop_path = os.path.join(self.vault_dir, shop_id)
                if os.path.exists(shop_path):
                    shutil.rmtree(shop_path)
                    print(f"✅ [Janitor] Successfully deleted {shop_path}")