import json
import torch
import os
import numpy as np
from sentence_transformers import SentenceTransformer, util

class DocumentSearch:
    def __init__(self, vectors_path="./data/vectors.jsonl", model_name="BAAI/bge-m3"):
        """Load the 1024-D vectors and the M4-optimized brain"""
        # 1. Hardware Setup
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"[Search] 🚀 Loading {model_name} on {self.device}...")
        
        self.model = SentenceTransformer(model_name, device=self.device)
        self.documents = []
        vectors_list = []
        
        # 2. Safety Check: Does the file exist?
        if not os.path.exists(vectors_path):
            print(f"❌ ERROR: Database not found at {vectors_path}. Run brain_builder first!")
            return

        # 3. Load the data
        with open(vectors_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    doc = json.loads(line)
                    # Extract the vector (1024 numbers)
                    if 'vector' in doc:
                        vector = doc.pop('vector')  
                        vectors_list.append(vector)
                        self.documents.append(doc)
        
        # 4. Final Validation
        if len(vectors_list) == 0:
            print("[Search] ⚠️ Database is empty! No vectors loaded.")
            self.vectors = None
        else:
            # Move vectors to M4 GPU memory
            self.vectors = torch.tensor(vectors_list, dtype=torch.float32).to(self.device)
            print(f"[Search] ✅ Ready! Loaded {len(self.documents)} documents.")
            print(f"[Search] Vector Brain Shape: {self.vectors.shape}")

    def search(self, query, top_k=3):
        if self.vectors is None:
            print("[Search] ❌ Cannot search: No vectors in memory.")
            return []

        print(f"\n[Search] Query: '{query}'")
        
        # 5. Multilingual Math (BGE-M3 + MPS)
        query_vector = self.model.encode(
            query, 
            convert_to_tensor=True, 
            device=self.device, 
            normalize_embeddings=True
        )
        
        # Calculate similarity on GPU
        similarities = util.cos_sim(query_vector, self.vectors)[0]
        
        # Get Top Results
        top_results = torch.topk(similarities, k=min(top_k, len(self.documents)))
        
        results = []
        for score, idx in zip(top_results.values, top_results.indices):
            idx = idx.item()
            doc = self.documents[idx].copy()
            score_val = float(score)
            
            # --- YOUR ORIGINAL DEBUGGING BLOCK ---
            found_keys = [k for k in doc.keys() if k not in ['search_en', 'context_uz']]
            print(f"  🎯 Score: {score_val:.3f}")
            print(f"      Metadata: {found_keys}")
            
            display_en = doc.get('search_en', 'No English found')
            display_uz = doc.get('context_uz', 'No Uzbek found')
            print(f"      EN: {display_en[:60]}...")
            print(f"      UZ: {display_uz[:60]}...")
            
            if 'price' in doc:
                print(f"      Price Tag: {doc['price']}")
            # --------------------------------------

            doc['score'] = score_val
            results.append(doc)
            
        return results

# --- TEST BLOCK ---
if __name__ == "__main__":
    searcher = DocumentSearch()
    
    test_queries = [
        "How long is delivery time?",
        "Menga suv o'tmaydigan kurtka kerak" # Uzbek Test!
    ]
    
    for q in test_queries:
        searcher.search(q, top_k=2)