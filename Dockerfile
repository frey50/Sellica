# 1. Use a slim Python image
FROM python:3.10-slim

# 2. Install system dependencies for FAISS and Git
RUN apt-get update && apt-get install -y \
    libgomp1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# 3. Set up a working directory
WORKDIR /app

# 4. Create a persistent home for models and set permissions
# We use /app/data/.cache as the home for HF models
RUN mkdir -p /app/data/.cache && chmod -R 777 /app/data
ENV HF_HOME=/app/data/.cache

# 5. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. 🔥 THE MAGIC STEP: Download the model during BUILD phase
# This ensures the model is physically inside the Docker image before it ships.
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

# 7. Copy the rest of your bot files
COPY . .

# 8. 🚫 FORCE OFFLINE MODE (Now it's safe because the model is inside)
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1
ENV PYTHONUNBUFFERED=1

# Hugging Face requires port 7860
EXPOSE 7860

# Start the bot
CMD ["python", "main.py"]