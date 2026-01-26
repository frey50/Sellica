# Use a slim Python image to keep the build fast
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (needed for Torch math)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project
COPY . .

# Railway uses the PORT environment variable automatically
CMD ["python", "main.py"]