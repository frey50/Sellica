import asyncio
import time
import os
import shutil
import logging
import gc
import config 

logger = logging.getLogger("Janitor")

class JanitorService:
    def __init__(self, registry, vault_dir=None, safety_service=None, interval=30, ttl=900):
        self.registry = registry          # Shared Shop Registry
        self.vault_dir = vault_dir or config.TEMP_VAULT
        self.safety_service = safety_service 
        self.interval = interval          
        self.ttl = ttl                    
        self.is_running = False

    async def start(self):
        if self.is_running: return
        self.is_running = True
        logger.info(f"🚀 [INIT] Janitor active on {self.vault_dir} | TTL: {self.ttl}s")
        
        try:
            while self.is_running:
                logger.info(f"🧐 [SCAN] Starting patrol cycle... ({len(self.registry)} items in registry)")
                await self._clean_cycle()
                await self._deep_sweep() 
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            logger.info("🛑 [SHUTDOWN] Janitor stopping...")
        finally:
            self.is_running = False

    def touch_shop(self, shop_id):
        """💓 DATASET HEARTBEAT: Keeps the shop 'Hot'."""
        if shop_id in self.registry:
            self.registry[shop_id]["time"] = time.time()
            logger.info(f"🔥 [HOT] Heartbeat for {shop_id}. Timer Reset.")
        else:
            # If this logs, it means the bot is trying to touch a shop that isn't loaded!
            logger.warning(f"❓ [MISS] Heartbeat received for {shop_id}, but not found in registry.")

    async def _clean_cycle(self):
        """Layer 1: The Registry Check (Find Cold Datasets)"""
        now = time.time()
        expired_shops = []

        # We use list() to safely iterate while we might delete items
        for shop_id, data in list(self.registry.items()):
            # CRITICAL: We only care about Shop IDs (Strings), not User IDs (Digits)
            if str(shop_id).isdigit():
                continue 

            last_used = data.get("time", 0)
            in_use = data.get("in_use", False)
            idle_time = now - last_used

            # 🛠️ TRACER: See exactly what the Janitor sees for every shop
            logger.info(f"📊 [STATUS] Shop: {shop_id} | Idle: {idle_time:.1f}s | In Use: {in_use}")

            if not in_use and (idle_time > self.ttl):
                logger.warning(f"❄️ [COLD] Shop {shop_id} has expired (Idle > {self.ttl}s).")
                expired_shops.append(shop_id)

        for shop_id in expired_shops:
            await self._wipe_shop(shop_id)

    async def _deep_sweep(self):
        """Layer 2: The Orphan Check (Find Leftover Folders)"""
        try:
            if not os.path.exists(self.vault_dir): return

            on_disk = [f for f in os.listdir(self.vault_dir) if os.path.isdir(os.path.join(self.vault_dir, f))]
            
            for folder in on_disk:
                if folder not in self.registry:
                    logger.warning(f"👻 [ORPHAN] Found folder '{folder}' with no owner in registry. Nuking...")
                    path = os.path.join(self.vault_dir, folder)
                    await asyncio.to_thread(shutil.rmtree, path, ignore_errors=True)
        except Exception as e:
            logger.error(f"⚠️ [DEEP_SWEEP ERROR] {e}")

    async def _wipe_shop(self, shop_id):
        """The Executioner: RAM to SSD cleanup."""
        try:
            # 1. RAM Eviction: Remove from dictionary so it's 'Cold' in memory
            if shop_id in self.registry:
                # We set searcher to None to help MacOS release the file handle
                if 'searcher' in self.registry[shop_id]:
                    self.registry[shop_id]['searcher'] = None
                del self.registry[shop_id]
                logger.info(f"🧠 [RAM] {shop_id} evicted from memory.")

            # 2. Unlock: Force Python to drop file locks
            gc.collect() 
            await asyncio.sleep(0.5) # Give MacOS a millisecond to breathe

            # 3. SSD Nuke
            shop_path = os.path.join(self.vault_dir, shop_id)
            if os.path.exists(shop_path):
                # We DON'T ignore errors here so we can see why it fails
                await asyncio.to_thread(shutil.rmtree, shop_path)
                
                # Check if it actually worked
                if not os.path.exists(shop_path):
                    logger.info(f"✅ [CLEAN] SSD wipe successful: {shop_id}")
                else:
                    logger.error(f"❌ [FAIL] Folder still exists: {shop_id}. MacOS lock detected!")
            
        except Exception as e:
            logger.error(f"💥 [FATAL] Error wiping {shop_id}: {e}")

    def stop(self):
        self.is_running = False