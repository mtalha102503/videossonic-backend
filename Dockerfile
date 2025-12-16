FROM python:3.9-slim

# 1. System Tools (FFmpeg + Curl zaroori hai)
RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Basic Requirements Install karein
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. MAGIC STEP: YT-DLP ko Seedha Master Branch se Install karo (Zip Method)
# Ye tareeqa "git" command se zyada reliable hai
RUN pip install --no-cache-dir --force-reinstall https://github.com/yt-dlp/yt-dlp/archive/master.zip

# 4. Baaki Code Copy
COPY . .

# 5. Server Start
