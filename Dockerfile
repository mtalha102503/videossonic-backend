FROM python:3.11-slim

# 1. System Tools (FFmpeg + Git + Curl + AtomicParsley)
# Added curl and atomicparsley for better download handling and metadata
RUN apt-get update && \
    apt-get install -y ffmpeg git curl atomicparsley && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Pip Upgrade
RUN pip install --no-cache-dir --upgrade pip

# 3. Basic Requirements Install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. FINAL SOLUTION: Install yt-dlp + Helper Libraries
# Added 'mutagen', 'websockets' and 'certifi' for secure connections
RUN pip install --no-cache-dir --force-reinstall \
    https://github.com/yt-dlp/yt-dlp/archive/master.zip \
    pycryptodomex \
    brotli \
    mutagen \
    websockets \
    certifi \
    requests

# 5. Copy Code
COPY . .

# 6. Server Start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
