import asyncio
import os
import time
from modules.data_manager import DataManager

async def test_lifecycle():
    # 1. Setup the Manager
    manager = DataManager(vault_dir="temp_vault")
    
    # START THE JANITOR in the background!
    janitor_task = asyncio.create_task(manager.janitor_task())
    
    print("🚀 --- TEST START: COLD BOOT ---")
    # This should trigger GitHub Pull -> Vectorize -> Save
    start_time = time.time()
    searcher = await manager.get_searcher("Classic_cargo")
    print(f"✅ Loaded Classic_cargo in {time.time() - start_time:.2f}s")
    
    # Verify folder exists on your Mac
    if os.path.exists("temp_vault/Classic_cargo"):
        print("📂 Verification: Folder created successfully.")

    print("\n⏳ Waiting 30 seconds... (Halfway to expiry)")
    await asyncio.sleep(30)
    
    print("🔥 --- TEST: RESET TIMER ---")
    # Accessing it again should reset the 60s clock
    await manager.get_searcher("Classic_cargo")
    print("🔄 Accessed Classic_cargo again. Janitor should wait another 60s.")

    print("\n⏳ Waiting 70 seconds for the Janitor to execute...")
    await asyncio.sleep(70)

    # FINAL CHECK
    if not os.path.exists("temp_vault/Classic_cargo"):
        print("\n🧹 SUCCESS: Janitor wiped the shop after 60s of silence!")
    else:
        print("\n❌ FAILURE: Shop still exists. Janitor is sleeping on the job.")

    # Cleanup: Stop the background task
    janitor_task.cancel()

if __name__ == "__main__":
    asyncio.run(test_lifecycle())