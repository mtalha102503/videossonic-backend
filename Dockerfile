FROM python:3.11-slim

# 1. System Tools (FFmpeg + Git zaroori hain)
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Pip Upgrade (Zaroori hai taake error na aaye)
RUN pip install --no-cache-dir --upgrade pip

# 3. Basic Requirements Install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. FINAL SOLUTION: Install yt-dlp + Helper Libraries (Brotli & PyCryptodomex)
# Ye libraries Facebook/TikTok ki encryption todne mein madad karti hain.
RUN pip install --no-cache-dir --force-reinstall https://github.com/yt-dlp/yt-dlp/archive/master.zip pycryptodomex brotli

# 5. Copy Code
COPY . .

# 6. Server Start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
