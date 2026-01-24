import json
import os
import logging
import time
from datetime import datetime

# Import your central configuration
import config 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [IRON_GUARD] - %(message)s'
)
logger = logging.getLogger("Safety")

class SafetyService:
    def __init__(self):
        """Uses paths defined in config.py for central data management."""
        # Using the absolute paths from config.py
        self.filepath = config.USER_REGISTRY
        self.data_dir = config.DATA_DIR
        
        if not os.path.exists(self.data_dir): 
            os.makedirs(self.data_dir)
            
        self.user_data = self._load_data()
        logger.info(f"🛡️ Iron Guard linked to registry: {self.filepath}")

    def _load_data(self):
        """Safe JSON loader."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except Exception: return {}
        return {}

    def _save_data(self):
        """Saves registry to disk."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.user_data, f, indent=4)
        except Exception as e: 
            logger.error(f"❌ Save Error: {e}")

    def _get_user(self, user_id):
        """Retrieves user stats and HEALS missing keys automatically."""
        uid = str(user_id)
        
        # Default structure
        defaults = {
            "sessions_used": 1,
            "msg_count": 0,
            "exhausted_at": 0,
            "total_msgs_lifetime": 0,
            "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        if uid not in self.user_data:
            self.user_data[uid] = defaults
        else:
            # This loop fixes the KeyError by adding any missing keys to existing users
            for key, value in defaults.items():
                if key not in self.user_data[uid]:
                    self.user_data[uid][key] = value
                    
        return self.user_data[uid]

    def check_access(self, user_id, text):
        """Tier 1: Checks message eligibility and triggers cooldown."""
        uid = str(user_id)
        user = self._get_user(uid)

        # 1. Length Check using config
        if not text or len(text.strip()) < config.MIN_MSG_LEN:
            return False, f"⚠️ Too short! (Min {config.MIN_MSG_LEN} chars)"

        # 2. FIXED KEY NAME HERE: changed 'exhaust_at' to 'exhausted_at'
        if user["exhausted_at"] > 0:
            time_passed = time.time() - user["exhausted_at"]
            if time_passed < config.RECHARGE_SECONDS:
                remaining = int(config.RECHARGE_SECONDS - time_passed)
                return False, f"🛑 Pack exhausted! Wait {remaining}s before your next pack."

        # 3. Check Session Limit
        if user["msg_count"] >= config.MSG_PER_SESSION:
            return False, "⚠️ Session finished! Type /start to move to your next session."

        # 4. SUCCESS: Allow & Update
        user["msg_count"] += 1
        user["total_msgs_lifetime"] += 1
        
        # Trigger "Final Strike" Timer if the entire pack is finished
        if user["sessions_used"] >= config.SESSIONS_PER_PACK and user["msg_count"] >= config.MSG_PER_SESSION:
            user["exhausted_at"] = time.time()
            logger.info(f"🔒 [LOCKDOWN] User {uid} finished the pack.")

        self._save_data()
        return True, "Success"

    def refresh_session(self, user_id):
        """Tier 2: Handles /start command."""
        uid = str(user_id)
        user = self._get_user(uid)
        now = time.time()

        # FIXED KEY NAME: exhausted_at (not exhaust_at)
        if user["exhausted_at"] > 0:
            time_passed = now - user["exhausted_at"]
            if time_passed < config.RECHARGE_SECONDS:
                remaining = int(config.RECHARGE_SECONDS - time_passed)
                return False, f"⏳ Recharging... Wait {remaining}s."
            else:
                user["sessions_used"] = 1
                user["msg_count"] = 0
                user["exhausted_at"] = 0
                self._save_data()
                return True, "🔋 Pack Restored! Session 1 ready."

        # CASE B: Session Refill (Moving from S1 to S2)
        if user["msg_count"] >= config.MSG_PER_SESSION:
            if user["sessions_used"] < config.SESSIONS_PER_PACK:
                user["sessions_used"] += 1
                user["msg_count"] = 0
                self._save_data()
                return True, f"⚡ Session {user['sessions_used']}/{config.SESSIONS_PER_PACK} activated!"
            
        return True, f"✅ Session {user['sessions_used']} active."

# ==========================================
# 🧪 DYNAMIC STRESS TESTER
# ==========================================
if __name__ == "__main__":
    print("\n" + "="*40)
    print("🚀 IRON GUARD DYNAMIC TEST")
    print(f"Limits: {config.SESSIONS_PER_PACK} Sessions | {config.MSG_PER_SESSION} Msgs")
    print("="*40)
    
    svc = SafetyService()
    T_ID = "TEST_CHAD_99"
    
    # Wipe test data
    if T_ID in svc.user_data: del svc.user_data[T_ID]
    
    # Step-by-step simulation
    print(f"1. Initializing: {svc.refresh_session(T_ID)[1]}")
    print(f"2. Msg 1: {svc.check_access(T_ID, 'Valid Input')[1]}")
    print(f"3. Msg 2: {svc.check_access(T_ID, 'Valid Input')[1]}")
    print(f"4. Block Check (S1 full): {svc.check_access(T_ID, 'Valid Input')[1]}")
    
    print(f"5. Refill to S2: {svc.refresh_session(T_ID)[1]}")
    
    print(f"6. Msg 3: {svc.check_access(T_ID, 'Valid Input')[1]}")
    print(f"7. Msg 4 (Final Strike): {svc.check_access(T_ID, 'Valid Input')[1]}")
    
    print(f"8. Immediate Block: {svc.refresh_session(T_ID)[1]}")
    
    print(f"\n⏳ Waiting halfway ({config.RECHARGE_SECONDS // 2}s)...")
    time.sleep(config.RECHARGE_SECONDS // 2)
    print(f"9. Mid-way Timer: {svc.refresh_session(T_ID)[1]}")
    
    print(f"⏳ Waiting for full reset...")
    time.sleep((config.RECHARGE_SECONDS // 2) + 1)
    print(f"10. Final Result: {svc.refresh_session(T_ID)[1]}")
    print("="*40 + "\n")