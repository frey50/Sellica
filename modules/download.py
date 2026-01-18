from sentence_transformers import SentenceTransformer
import torch

# This tells the model: "Hey, use my M4 GPU!"
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"📡 Downloading BGE-M3 to your M4... hang tight.")
model = SentenceTransformer('BAAI/bge-m3', device=device)
print("✅ Brain is now living on your Mac locally.")