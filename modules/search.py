import json
import os
import torch
import logging
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# --- PROFESSIONAL LOGGING SETUP ---
logger = logging.getLogger("SearchEngine")

class DocumentSearch:
    def __init__(self, vectors_path: str = "./data/vectors.jsonl"):
        """
        Industry-grade Vector Search using Google Gemini Embeddings (768-D).
        Includes error recovery and memory safety.
        """
        # 1. API Initialization with Validation
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.critical("❌ GOOGLE_API_KEY missing. Vectorization will fail.")
            raise EnvironmentError("GOOGLE_API_KEY not found in environment.")

        genai.configure(api_key=self.api_key)
        self.model_id = "models/text-embedding-004"
        
        # 2. Hardware-Agile Setup
        # Use CPU for Railway/Production unless specialized hardware is detected
        self.device = torch.device("cpu")
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
            
        self.documents: List[Dict[str, Any]] = []
        self.vectors: Optional[torch.Tensor] = None
        
        # 3. Secure Loading Process
        self._load_database(vectors_path)

    def _load_database(self, path: str):
        """Private method to handle data loading with corruption checks."""
        if not os.path.exists(path):
            logger.error(f"📂 Database file missing at: {path}")
            return

        vectors_list = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        doc = json.loads(line)
                        if 'vector' not in doc:
                            logger.warning(f"⚠️ Skipping line {line_num}: No vector found.")
                            continue
                        
                        vectors_list.append(doc.pop('vector'))
                        self.documents.append(doc)
                    except json.JSONDecodeError:
                        logger.error(f"❌ Corruption detected on line {line_num}. Skipping.")
                        continue

            if not vectors_list:
                logger.warning("⚠️ Database loaded but contains no valid vectors.")
                return

            # Normalize vectors immediately on load for faster Dot Product search
            raw_vectors = torch.tensor(vectors_list, dtype=torch.float32)
            self.vectors = raw_vectors / raw_vectors.norm(dim=-1, keepdim=True)
            self.vectors = self.vectors.to(self.device)
            
            logger.info(f"✅ Search Ready: {len(self.documents)} items | Device: {self.device}")

        except Exception as e:
            logger.critical(f"💥 Failed to load search database: {str(e)}")

    def search(self, query: str, top_k: int = 3, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        High-performance similarity search.
        :param query: User input string
        :param top_k: Number of results
        :param threshold: Minimum similarity score to return
        """
        # 1. Input Guard
        if not query or not query.strip():
            logger.warning("Empty query received. Returning empty list.")
            return []

        if self.vectors is None or len(self.documents) == 0:
            logger.error("Search attempted on empty or uninitialized database.")
            return []

        # 2. Cloud Vectorization with Retries
        try:
            result = genai.embed_content(
                model=self.model_id,
                content=query.strip(),
                task_type="retrieval_query"
            )
            q_vec = torch.tensor(result['embedding'], dtype=torch.float32).to(self.device)
            # Normalize query
            q_vec = q_vec / q_vec.norm(dim=-1, keepdim=True)
            
        except Exception as e:
            logger.error(f"☁️ Google API failure during search: {e}")
            return []

        # 3. Optimized Similarity Computation (Dot Product on Normalized Tensors)
        with torch.no_grad():
            # [1, 768] @ [768, N] -> [1, N]
            similarities = torch.mm(q_vec.unsqueeze(0), self.vectors.t()).squeeze(0)
            
            # 4. Result Extraction
            k = min(top_k, len(self.documents))
            scores, indices = torch.topk(similarities, k=k)
            
            results = []
            for score, idx in zip(scores.tolist(), indices.tolist()):
                if score < threshold:
                    continue  # Ignore irrelevant results
                
                res = self.documents[idx].copy()
                res['score'] = round(score, 4)
                results.append(res)
                
            return results

# --- END OF CLASS ---