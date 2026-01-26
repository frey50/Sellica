import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class DocumentVectorizer:
    def __init__(self):
        # Setup Google Auth
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        
        # This model is ALWAYS warm - no cold starts!
        self.model_id = "models/text-embedding-004"
        print(f"[Vectorizer] 🚀 Connected to Google Instant Embeddings")

    def vectorize_documents(self, documents, output_path="./data/vectors.jsonl"):
        if not documents:
            return []

        # 1. Prepare texts
        texts = [doc.get("search_en", doc.get("content", "")).strip() for doc in documents]
        
        print(f"[Vectorizer] 🧠 Embedding {len(texts)} items (Uzbek/Russian/English support)...")

        # 2. Batch Request to Google (Zero Cold Start)
        try:
            result = genai.embed_content(
                model=self.model_id,
                content=texts,
                task_type="retrieval_document"
            )
            # Google returns a list of vectors in ['embeddings']
            all_vectors = result['embedding']
        except Exception as e:
            print(f"[Vectorizer] ❌ Google API Error: {e}")
            return []

        # 3. Bundle and Save
        vectorized_docs = []
        for i, doc in enumerate(documents):
            new_doc = doc.copy()
            new_doc["vector"] = all_vectors[i]
            vectorized_docs.append(new_doc)

        out_file = Path(output_path)
        out_file.parent.mkdir(exist_ok=True, parents=True)
        
        with open(out_file, 'w', encoding='utf-8') as f:
            for d in vectorized_docs:
                f.write(json.dumps(d, ensure_ascii=False) + '\n')
        
        print(f"[Vectorizer] ✅ SUCCESS: Saved to {out_file}")
        return vectorized_docs

if __name__ == "__main__":
    # Quick Test for Uzbek/Russian
    test_docs = [
        {"id": "uz_1", "content": "Suv o'tmaydigan shim"}, # Uzbek
        {"id": "ru_1", "content": "Водонепроницаемые брюки"} # Russian
    ]
    v = DocumentVectorizer()
    v.vectorize_documents(test_docs)