FROM python:3.9-slim

# System updates + FFmpeg + Git (Zaroori hai latest update ke liye)
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements install karein
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baaki code copy karein
COPY . .

# Server start karein
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
