import json
import os
import torch
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class DocumentSearch:
    def __init__(self, vectors_path="./data/vectors.jsonl"):
        """Load the 768-D vectors and connect to Google Cloud Brain"""
        # 1. Setup Google API (No local model loading = No RAM issues!)
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        self.model_id = "models/text-embedding-004"
        
        # 2. Hardware Setup (Still using MPS for the similarity math if available)
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        
        self.documents = []
        vectors_list = []
        
        # 3. Safety Check: Does the file exist?
        if not os.path.exists(vectors_path):
            print(f"❌ ERROR: Database not found at {vectors_path}. Run DataManager first!")
            self.vectors = None
            return

        # 4. Load the 768-D Google Vectors
        print(f"[Search] 📂 Loading vectors from {vectors_path}...")
        with open(vectors_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    doc = json.loads(line)
                    if 'vector' in doc:
                        vector = doc.pop('vector')  
                        vectors_list.append(vector)
                        self.documents.append(doc)
        
        # 5. Move vectors to GPU memory
        if len(vectors_list) == 0:
            print("[Search] ⚠️ Database is empty!")
            self.vectors = None
        else:
            self.vectors = torch.tensor(vectors_list, dtype=torch.float32).to(self.device)
            print(f"[Search] ✅ Ready! Loaded {len(self.documents)} documents.")
            print(f"[Search] 🧠 Vector Shape: {self.vectors.shape} (768-D Google)")

    def search(self, query, top_k=3):
        if self.vectors is None:
            return []

        print(f"\n[Search] Query: '{query}'")
        
        # 6. CLOUD VECTORIZATION (Instant & Multilingual)
        try:
            # Note: task_type="retrieval_query" is key for better search results!
            result = genai.embed_content(
                model=self.model_id,
                content=query,
                task_type="retrieval_query"
            )
            query_vector = torch.tensor(result['embedding'], dtype=torch.float32).to(self.device)
        except Exception as e:
            print(f"[Search] ❌ Google API Error: {e}")
            return []
        
        # 7. Similarity Math (Cos Sim)
        # We normalize vectors to use simple dot product (which is faster)
        query_norm = query_vector / query_vector.norm(dim=-1, keepdim=True)
        vectors_norm = self.vectors / self.vectors.norm(dim=-1, keepdim=True)
        
        similarities = torch.mm(query_norm.unsqueeze(0), vectors_norm.t()).squeeze(0)
        
        # 8. Get Top Results
        top_results = torch.topk(similarities, k=min(top_k, len(self.documents)))
        
        results = []
        for score, idx in zip(top_results.values, top_results.indices):
            idx = idx.item()
            doc = self.documents[idx].copy()
            doc['score'] = float(score)
            
            # --- DEBUG LOGS (Keeping your style) ---
            print(f"  🎯 Score: {doc['score']:.3f}")
            print(f"      EN: {doc.get('search_en', 'N/A')[:50]}...")
            if 'price' in doc:
                print(f"      Price: {doc['price']}")
            
            results.append(doc)
            
        return results

if __name__ == "__main__":
    # Test with your Google setup
    searcher = DocumentSearch(vectors_path="./data/vectors.jsonl")
    searcher.search("Suv o'tmaydigan kurtka")