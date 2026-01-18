"""
GitHub Loader Module - FLATTENED VERSION
Fetches shop data and ensures no nesting for higher productivity
"""

import requests
import json
from config import GITHUB_TOKEN, DEBUG_MODE


def load_docs(shop_name):
    """
    Main function to load all documents for a shop
    Ensures all keys are TOP-LEVEL (Flattened)
    """
    if DEBUG_MODE:
        print(f"\n[GitHub Loader] 🚀 Fetching data for: {shop_name}")
    
    repo_owner = "frey50"
    repo_name = "DATAINC"
    base_path = "Datasets"
    
    # 1. Fetch raw data
    faqs_raw = _fetch_file(shop_name, "faqs.jsonl", repo_owner, repo_name, base_path)
    products_raw = _fetch_file(shop_name, "products.jsonl", repo_owner, repo_name, base_path)
    
    documents = []
    
    # --- DEBUGGER: Check raw keys before transformation ---
    if faqs_raw and DEBUG_MODE:
        print(f"[GitHub Loader] 🔍 Sample FAQ keys from GitHub: {list(faqs_raw[0].keys())}")
    
    # 2. Process FAQs (FLATTENING)
    for item in faqs_raw:
        # We start with a flat dict
        doc = {
            "file": "faqs.jsonl",
            "type": "faq",
            "source_path": f"{base_path}/{shop_name}/faqs.jsonl"
        }
        # BRUHH: This line is the magic. It takes everything in 'item' 
        # and puts it on the top level of 'doc'
        doc.update(item) 
        documents.append(doc)
    
    # 3. Process Products (FLATTENING)
    for item in products_raw:
        doc = {
            "file": "products.jsonl",
            "type": "product",
            "source_path": f"{base_path}/{shop_name}/products.jsonl"
        }
        doc.update(item)
        documents.append(doc)

    # --- FINAL DEBUGGER: The 'Contract' Check ---
    if DEBUG_MODE and documents:
        print(f"[GitHub Loader] ✅ Successfully flattened {len(documents)} documents.")
        print(f"[GitHub Loader] 🔍 Final Document Sample Keys: {list(documents[0].keys())}")
        if 'search_en' not in documents[0]:
            print(f"[GitHub Loader] ⚠️ WARNING: 'search_en' missing at top level!")
    
    return documents


def _fetch_file(shop_name, filename, repo_owner, repo_name, base_path):
    """Internal function to fetch and parse JSONL from GitHub"""
    file_path = f"{base_path}/{shop_name}/{filename}"
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        
        data = []
        for line in response.text.strip().split('\n'):
            if line.strip():
                data.append(json.loads(line))
        return data
    except Exception as e:
        print(f"[GitHub Loader] ❌ Error: {e}")
        return []

# Test it
if __name__ == "__main__":
    DEBUG_MODE = True
    print("=" * 50)
    docs = load_docs("Techwear_shop")
    
    if docs:
        print("\n--- FINAL VERIFICATION ---")
        # If this prints 'search_en', we won!
        print(f"Top-level keys found: {list(docs[0].keys())}")
        print(f"Content Check (search_en): {docs[0].get('search_en', 'MISSING')[:50]}...")