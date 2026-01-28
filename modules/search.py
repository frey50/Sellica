import json
import os
import torch
import logging
import time
from pathlib import Path
from google import genai
from google.genai import types
from typing import List, Dict, Any, Optional
import config

logger = logging.getLogger("SearchEngine")

class DocumentSearch:
    def __init__(self, shop_id: str):
        """
        Industry-grade Vector Search with Confidence Scoring.
        Forced for 2026: v1beta, 768-D, and Cosine-to-Percentage mapping.
        """
        self.vectors_path = config.TEMP_VAULT / shop_id / "vectors.jsonl"
        
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.critical("❌ GOOGLE_API_KEY missing!")
            raise EnvironmentError("GOOGLE_API_KEY not found.")

        # Client setup matches the Vectorizer
        self.client = genai.Client(
            api_key=self.api_key,
            http_options={'api_version': 'v1beta'}
        )
        self.model_id = "gemini-embedding-001" 
        
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
                return

            raw_vectors = torch.tensor(vectors_list, dtype=torch.float32)
            
            # 🛡️ Safety: Normalize so Dot Product = Cosine Similarity
            self.vectors = raw_vectors / raw_vectors.norm(dim=-1, keepdim=True)
            self.vectors = self.vectors.to(self.device)
            
            logger.info(f"✅ [READY] {len(self.documents)} items. Device: {self.device}")

        except Exception as e:
            logger.critical(f"💥 Database Load Failed: {e}")

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
        if self.vectors is None or not self.documents:
            return []

        clean_query = query.strip()
        if not clean_query:
            return []

        # 1. Embed Query with Retry Logic
        q_values = None
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
                time.sleep((attempt + 1) * 2)

        if not q_values:
            return []

        # 2. Vector Search Logic
        try:
            q_vec = torch.tensor(q_values, dtype=torch.float32).to(self.device)
            # Normalize query vector
            q_vec = q_vec / q_vec.norm(dim=-1, keepdim=True)
            
            with torch.no_grad():
                # MM calculates Dot Product (Cosine Similarity since both are normalized)
                # Equation: $$similarity = \frac{A \cdot B}{\|A\| \|B\|}$$
                similarities = torch.mm(q_vec.unsqueeze(0), self.vectors.t()).squeeze(0)
                
                k = min(top_k, len(self.documents))
                scores, indices = torch.topk(similarities, k=k)
                
                results = []
                for score, idx in zip(scores.tolist(), indices.tolist()):
                    if score >= threshold:
                        res = self.documents[idx].copy()
                        # Add Accuracy metrics
                        res['score'] = round(score, 4)
                        res['accuracy'] = f"{round(score * 100, 1)}%"
                        res['label'] = self._get_label(score)
                        results.append(res)
                
                return results

        except Exception as e:
            logger.error(f"💥 Search Error: {e}")
            return []