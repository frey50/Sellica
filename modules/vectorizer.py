import os
import json
import logging
import time
from pathlib import Path
from google import genai
from google.genai import types

logger = logging.getLogger("Vectorizer")

class DocumentVectorizer:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found.")
        
        self.client = genai.Client(
            api_key=self.api_key,
            http_options={'api_version': 'v1beta'} 
        )
        self.model_id = "gemini-embedding-001"
        
        # Industry Standards for 2026
        self.MAX_BATCH_SIZE = 250  # Google's hard limit per request
        self.MAX_RETRIES = 3

    def _chunk_list(self, data, size):
        """Splits a large list into smaller chunks for the API."""
        for i in range(0, len(data), size):
            yield data[i:i + size]

    def vectorize_documents(self, docs, output_path):
        if not docs:
            logger.warning("⚠️ Empty document list provided.")
            return []

        vectorized_docs = []
        
        # 1. Chunking to avoid "Request payload too large"
        chunks = list(self._chunk_list(docs, self.MAX_BATCH_SIZE))
        logger.info(f"🧠 [VECTORS] Processing {len(docs)} items in {len(chunks)} batch(es)...")

        for chunk_idx, chunk in enumerate(chunks):
            input_texts = [
                f"{d.get('search_en', '')} {d.get('context_uz', '')}".strip() 
                for d in chunk
            ]

            # 2. Robust Retry Logic (Exponential Backoff)
            success = False
            for attempt in range(self.MAX_RETRIES):
                try:
                    response = self.client.models.embed_content(
                        model=self.model_id,
                        contents=input_texts,
                        config=types.EmbedContentConfig(
                            task_type="RETRIEVAL_DOCUMENT",
                            output_dimensionality=768
                        )
                    )
                    
                    # Map results back to local copies
                    for i, doc in enumerate(chunk):
                        doc_copy = doc.copy()
                        doc_copy['vector'] = response.embeddings[i].values
                        vectorized_docs.append(doc_copy)
                    
                    success = True
                    break # Success! Move to next chunk.

                except Exception as e:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"⏳ [RETRY {attempt+1}] API Busy/Error: {e}. Waiting {wait_time}s...")
                    time.sleep(wait_time)

            if not success:
                logger.error(f"❌ [FATAL] Failed to vectorize batch {chunk_idx + 1} after {self.MAX_RETRIES} attempts.")
                return [] # Return empty to trigger system safety

        # 3. Secure Atomic Save
        try:
            out_file = Path(output_path)
            out_file.parent.mkdir(exist_ok=True, parents=True)
            
            with open(out_file, 'w', encoding='utf-8') as f:
                for d in vectorized_docs:
                    f.write(json.dumps(d, ensure_ascii=False) + '\n')
            
            logger.info(f"✅ [SUCCESS] Saved {len(vectorized_docs)} vectors to disk.")
            return vectorized_docs

        except Exception as e:
            logger.error(f"❌ [FILE ERROR] Failed to save JSONL: {e}")
            return []