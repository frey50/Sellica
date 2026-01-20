import requests
import json
import logging
from config import GITHUB_TOKEN, DEBUG_MODE

# Set up logging for this module
logger = logging.getLogger(__name__)

def list_remote_shops():
    repo_owner = "frey50"
    repo_name = "DATAINC"
    base_path = "Datasets" # ⚠️ DOUBLE CHECK: Is it 'Datasets' or 'datasets' on GitHub?
    
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{base_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        
        # 🛡️ HARDENING: Tell us EXACTLY why it failed
        if response.status_code != 200:
            error_msg = response.json().get('message', 'Unknown Error')
            print(f"❌ [Loader] GitHub API Error ({response.status_code}): {error_msg}")
            if response.status_code == 401:
                print("🔑 [Check]: Your GITHUB_TOKEN might be invalid or expired.")
            if response.status_code == 404:
                print(f"📂 [Check]: Path '{base_path}' not found. Check uppercase/lowercase!")
            return []

        contents = response.json()
        
        # Filter: only keep items that are 'dir' (folders)
        shops = [item['name'] for item in contents if item['type'] == 'dir']
        
        if DEBUG_MODE:
            print(f"📂 [Loader] Discovered {len(shops)} shops: {shops}")
            
        return shops

    except Exception as e:
        print(f"❌ [Loader] Critical Network Error: {e}")
        return []

def load_docs(shop_id):
    repo_owner = "frey50"
    repo_name = "DATAINC"
    base_path = f"Datasets/{shop_id}"
    
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{base_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []

        folder_contents = response.json()
        all_documents = []

        for file_info in folder_contents:
            filename = file_info['name']
            if filename.endswith(('.json', '.jsonl')):
                raw_items = _fetch_raw_content(file_info['download_url'], filename)
                
                for item in raw_items:
                    # 🛡️ SWISS WATCH: Ensure item is a dictionary
                    if isinstance(item, dict):
                        doc = {
                            "shop_id": shop_id,
                            "file_source": filename,
                            "data_type": filename.split('.')[0]
                        }
                        doc.update(item)
                        all_documents.append(doc)
        return all_documents
    except Exception as e:
        print(f"❌ [Loader] load_docs error: {e}")
        return []

def _fetch_raw_content(download_url, filename):
    """🛡️ HARDENED: Handles both standard JSON and JSONL"""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    try:
        resp = requests.get(download_url, headers=headers, timeout=10)
        if resp.status_code != 200: 
            return []

        # 🚀 SMART LOADING
        if filename.endswith('.jsonl'):
            data = []
            for line in resp.text.strip().split('\n'):
                if line.strip():
                    data.append(json.loads(line))
            return data
        else:
            # It's a standard .json file (likely a list)
            return resp.json() 

    except Exception as e:
        print(f"❌ [Fetch Error] {filename}: {e}")
        return []
    
    # --- THE ULTIMATE TEST BLOCK ---
if __name__ == "__main__":
    print("\n🔍 [Test] Starting Manual GitHub Scan...")
    
    # 1. Test the Shop List
    shops = list_remote_shops()
    
    if not shops:
        print("❌ [Test] list_remote_shops() returned an EMPTY list.")
        print(f"👉 Check: Does 'Datasets' folder exist in repo 'frey50/DATAINC'?")
    else:
        print(f"✅ [Test] Found {len(shops)} shops: {shops}")
        
        # 2. Test Loading Docs for the first shop found
        target_shop = shops[0]
        print(f"🔍 [Test] Attempting to pull docs from: {target_shop}...")
        docs = load_docs(target_shop)
        
        if not docs:
            print(f"❌ [Test] Failed to load any documents from {target_shop}.")
        else:
            print(f"🔥 [Test] SUCCESS! Loaded {len(docs)} docs from {target_shop}.")
            print(f"📝 Sample Data: {str(docs[0])[:200]}...")