import json
import os
import torch
import logging
import time
import traceback
from pathlib import Path
from google import genai
from google.genai import types
from typing import List, Dict, Any, Optional
import config

# 🎯 Centralized Logging
logger = logging.getLogger("SearchEngine")

class DocumentSearch:
    def __init__(self, shop_id: str):
        """
        Industry-grade Vector Search with Confidence Scoring.
        Forced for 2026: v1beta, 768-D, and Cosine-to-Percentage mapping.
        """
        self.shop_id = shop_id
        self.vectors_path = config.TEMP_VAULT / shop_id / "vectors.jsonl"
        
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.critical(f"❌ [AUTH] GOOGLE_API_KEY missing for search in {shop_id}!")
            raise EnvironmentError("GOOGLE_API_KEY not found.")

        # Client setup matches the Vectorizer
        try:
            self.client = genai.Client(
                api_key=self.api_key,
                http_options={'api_version': 'v1beta'}
            )
            self.model_id = "gemini-embedding-001" 
            logger.info(f"✅ [INIT] Search Engine ready for {shop_id} using {self.model_id}")
        except Exception as e:
            logger.error(f"💥 [INIT_FAIL] GenAI Client error: {e}")
            raise

        # Device Auto-Detection
        self.device = torch.device("cpu")
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
            
        self.documents: List[Dict[str, Any]] = []
        self.vectors: Optional[torch.Tensor] = None
        self.MAX_RETRIES = 3
        
        self._load_database()

    def _load_database(self):
        """Loads and normalizes vectors for fast Dot Product search."""
        if not self.vectors_path.exists():
            logger.warning(f"⚠️ [MISSING] No vectors found at {self.vectors_path}")
            return

        vectors_list = []
        try:
            with open(self.vectors_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        doc = json.loads(line)
                        if 'vector' in doc:
                            vectors_list.append(doc.pop('vector'))
                            self.documents.append(doc)
                    except json.JSONDecodeError:
                        continue 

            if not vectors_list:
                logger.error(f"🚨 [EMPTY_FILE] {self.vectors_path} contains no valid vectors.")
                return

            # 📍 JUNCTION: Tensor Preparation
            raw_vectors = torch.tensor(vectors_list, dtype=torch.float32)
            
            # 🛡️ Safety: Normalize so Dot Product = Cosine Similarity
            self.vectors = raw_vectors / raw_vectors.norm(dim=-1, keepdim=True)
            self.vectors = self.vectors.to(self.device)
            
            logger.info(f"✅ [READY] Loaded {len(self.documents)} items into {self.device} memory.")

        except Exception as e:
            logger.critical(f"💥 [DB_LOAD_FAIL] {self.shop_id}: {e}")
            logger.debug(traceback.format_exc())

    def _get_label(self, score: float) -> str:
        """Categorizes the match confidence for the user."""
        if score >= 0.85: return "🎯 High Confidence"
        if score >= 0.70: return "✅ Good Match"
        if score >= 0.50: return "🔍 Partial Match"
        return "❓ Low Confidence"

    def search(self, query: str, top_k: int = 3, threshold: float = 0.35) -> List[Dict[str, Any]]:
        """
        Returns results with a 'score' and 'confidence_label'.
        """
        # 🛡️ Guard 1: Empty Registry
        if self.vectors is None or not self.documents:
            logger.warning(f"⚠️ [SEARCH_VOID] No vectors loaded for {self.shop_id}. Returning empty results.")
            return []

        clean_query = query.strip()
        if not clean_query:
            return []

        # 1. Embed Query with Retry Logic
        q_values = None
        logger.info(f"📡 [EMBED] Generating vector for query: '{clean_query[:30]}...'")
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.models.embed_content(
                    model=self.model_id,
                    contents=clean_query,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_QUERY",
                        output_dimensionality=768
                    )
                )
                q_values = response.embeddings[0].values
                break
            except Exception as e:
                logger.error(f"🔄 [RETRY {attempt+1}] Embedding failed: {e}")
                if attempt == self.MAX_RETRIES - 1:
                    logger.critical("❌ [EMBED_FAIL] All retries exhausted.")
                    return []
                time.sleep((attempt + 1) * 2)

        # 2. Vector Search Logic
        try:
            q_vec = torch.tensor(q_values, dtype=torch.float32).to(self.device)
            
            # 🛡️ Guard 2: Dimension Check
            if q_vec.shape[0] != 768:
                logger.error(f"🚨 [DIM_MISMATCH] Query vector is {q_vec.shape[0]}D, but manifest is 768D.")
                return []

            # Normalize query vector for Cosine Similarity
            q_vec = q_vec / q_vec.norm(dim=-1, keepdim=True)
            
            with torch.no_grad():
                # Similarity Calculation: $$similarity = \frac{A \cdot B}{\|A\| \|B\|}$$
                # Since both are normalized, it simplifies to Dot Product.
                similarities = torch.mm(q_vec.unsqueeze(0), self.vectors.t()).squeeze(0)
                
                k = min(top_k, len(self.documents))
                scores, indices = torch.topk(similarities, k=k)
                
                results = []
                logger.info(f"🧐 [MATH] Top score for '{self.shop_id}': {scores[0].item():.4f}")

                for score, idx in zip(scores.tolist(), indices.tolist()):
                    if score >= threshold:
                        res = self.documents[idx].copy()
                        res['score'] = round(score, 4)
                        res['accuracy'] = f"{round(score * 100, 1)}%"
                        res['label'] = self._get_label(score)
                        results.append(res)
                
                if not results:
                    logger.warning(f"🔍 [NO_MATCH] Best score {scores[0].item():.4f} was below threshold {threshold}")
                
                return results

        except Exception as e:
            logger.error(f"💥 [SEARCH_CRASH] Mathematical error during top-k: {e}")
            logger.debug(traceback.format_exc())
            return []