FROM python:3.11-slim

# 1. System Tools: FFmpeg, Git, Curl, AtomicParsley ke sath TOR aur PRIVOXY add kiya
# Tor: IP chupane ke liye
# Privoxy: Tor ko HTTP proxy ki tarah use karne ke liye
RUN apt-get update && \
    apt-get install -y ffmpeg git curl atomicparsley tor privoxy && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Configure Tor & Privoxy (Ghost Setup)
# Privoxy ko Tor (port 9050) se connect karte hain
RUN echo "forward-socks5t / 127.0.0.1:9050 ." >> /etc/privoxy/config
# Privoxy port 8118 par chalega
RUN sed -i 's/listen-address  127.0.0.1:8118/listen-address  0.0.0.0:8118/' /etc/privoxy/config

# 3. Pip Upgrade
RUN pip install --no-cache-dir --upgrade pip

# 4. Basic Requirements Install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Install yt-dlp + Helper Libraries
RUN pip install --no-cache-dir --force-reinstall \
    https://github.com/yt-dlp/yt-dlp/archive/master.zip \
    pycryptodomex \
    brotli \
    mutagen \
    websockets \
    certifi \
    requests \
    pysocks

# 6. Copy Code
COPY . .

# 7. Create Startup Script (Tor, Privoxy, aur App ek sath chalane ke liye)
# Ye script pehle Tor aur Privoxy start karega, phir app chalayega
RUN echo "#!/bin/bash\n\
service tor start\n\
service privoxy start\n\
uvicorn main:app --host 0.0.0.0 --port 8000" > /app/start.sh && chmod +x /app/start.sh

# 8. Start Everything
CMD ["/app/start.sh"]
