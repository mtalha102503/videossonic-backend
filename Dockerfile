FROM python:3.9-slim

# 1. System Tools (FFmpeg + Curl + Unzip zaroori hain)
RUN apt-get update && \
    apt-get install -y ffmpeg curl unzip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Basic Requirements Install karein (yt-dlp ke ilawa)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 3. ROBUST INSTALL: Download & Install yt-dlp from Zip (No Git needed)
# Pehle zip download karo
RUN curl -L -o yt-dlp.zip https://github.com/yt-dlp/yt-dlp/archive/master.zip
# Phir unzip karo
RUN unzip yt-dlp.zip
# Folder ka naam 'yt-dlp-master' hota hai, wahan se install karo
RUN pip install --no-cache-dir ./yt-dlp-master
# Safai (Zip aur folder delete karo)
RUN rm -rf yt-dlp.zip yt-dlp-master

# 4. Baaki Code Copy
COPY . .

# 5. Server Start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
