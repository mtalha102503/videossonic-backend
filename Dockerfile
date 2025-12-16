FROM python:3.9-slim

# 1. System Tools (FFmpeg + Git zaroori hai)
# Git is required for pip to install from GitHub directly
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Basic Requirements Install karein
COPY requirements.txt .
# Upgrade pip first to avoid errors
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 3. MAGIC STEP: Install Latest yt-dlp using Git
# This pulls the absolute latest code to fix Facebook/TikTok errors
RUN pip install --no-cache-dir --force-reinstall git+https://github.com/yt-dlp/yt-dlp.git@master

# 4. Baaki Code Copy
COPY . .

# 5. Server Start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
