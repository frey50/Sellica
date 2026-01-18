import json
import torch # Added for M4 support
from pathlib import Path
from sentence_transformers import SentenceTransformer

class DocumentVectorizer:
    def __init__(self, model_name="BAAI/bge-m3"): # Step 1: Upgrade Model
        # Step 2: Detect M4 Metal GPU
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"[Vectorizer] 🏎️ Loading {model_name} on {self.device}...")
        
        # Load the model directly to the M4 GPU
        self.model = SentenceTransformer(model_name, device=self.device)
        print(f"[Vectorizer] Model loaded! ✅")

    def vectorize_documents(self, documents, output_path="./data/vectors.jsonl"):
        if not documents:
            print("[Vectorizer] ❌ Error: No documents provided!")
            return []

        print(f"\n[Vectorizer] 🚀 Processing {len(documents)} documents on M4...")
        
        vectorized_docs = []
        
        # Optimization: We extract all text first to do 'Batch Encoding'
        # This is 10x faster than a loop for big datasets
        texts_to_embed = []
        for doc in documents:
            text = doc.get("search_en", doc.get("content", "")).strip()
            texts_to_embed.append(text)

        # Step 3: High-Performance Batch Encoding
        # normalize_embeddings=True makes search much more reliable
        print(f"[Vectorizer] 🧠 Encoding {len(texts_to_embed)} docs (1024-D)...")
        all_vectors = self.model.encode(
            texts_to_embed, 
            batch_size=32, 
            show_progress_bar=True, 
            normalize_embeddings=True
        )

        # Step 4: Re-bundle the docs with the new math
        for i, doc in enumerate(documents):
            new_doc = doc.copy()
            new_doc["vector"] = all_vectors[i].tolist() 
            vectorized_docs.append(new_doc)

        # Step 5: Save (Keeping your ensure_ascii=False for Uzbek characters)
        out_file = Path(output_path)
        out_file.parent.mkdir(exist_ok=True, parents=True)
        
        print(f"[Vectorizer] 💾 Saving to {out_file}...")
        with open(out_file, 'w', encoding='utf-8') as f:
            for d in vectorized_docs:
                f.write(json.dumps(d, ensure_ascii=False) + '\n')
        
        print(f"[Vectorizer] ✅ SUCCESS: 1024-D Multilingual brain is ready.")
        return vectorized_docs

# --- INTEGRATION TEST ---
if __name__ == "__main__":
    mock_docs = [
        {"id": "p_1", "search_en": "Waterproof jacket", "context_uz": "Suv o'tmaydigan kurtka"},
        {"id": "p_2", "search_en": "Cotton t-shirt", "context_uz": "Paxtali futbolka"}
    ]
    
    vectorizer = DocumentVectorizer()
    results = vectorizer.vectorize_documents(mock_docs)
    
    if results:
        # Should now be 1024!
        print(f"\n[Check] New Vector Size: {len(results[0]['vector'])}")