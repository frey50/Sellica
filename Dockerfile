# Use a slim Python image to keep the build fast
FROM python:3.10-slim

# Install system dependencies for FAISS and Git
RUN apt-get update && apt-get install -y \
    libgomp1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set up a working directory
WORKDIR /app

# Copy and install dependencies first (faster rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your bot files
COPY . .

# 🚫 FORCE OFFLINE MODE 
# Since you have the model on your MacBook, the cloud will download it ONCE 
# during build, then use it locally.
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

# Hugging Face requires port 7860 to be exposed even for bots
EXPOSE 7860

# Start the bot
CMD ["python", "main.py"]