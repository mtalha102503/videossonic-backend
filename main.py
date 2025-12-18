from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import yt_dlp
import urllib.parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestModel(BaseModel):
    url: str
    quality: str = "1080"

# Info Route
@app.post("/get-info")
async def get_info(request: RequestModel):
    ydl_opts = {'quiet': True, 'nocheckcertificate': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            return {
                "status": "success",
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail'),
                "platform": info.get('extractor_key')
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 🔥 FINAL ENDPOINT (POST) 🔥 ---
# Ye 'GET' nahi 'POST' hai. 404 nahi aayega kyunki get-info bhi POST hai aur wo chal rha hai.
@app.post("/download-video")
async def download_video(request: RequestModel):
    
    # 1. Clean Title
    video_title = "VideosSonic_Video"
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(request.url, download=False)
            video_title = info.get('title', 'video').replace('"', '').replace("'", "").replace(" ", "_")
    except:
        pass

    ext = "mp3" if request.quality == 'audio' else "mp4"
    encoded_filename = urllib.parse.quote(f"{video_title[:50]}.{ext}")

    # 2. Universal Stream Command (No Redirects)
    # TikTok/FB/Insta sab yahan se guzrenge
    cmd = [
        "yt-dlp",
        "--output", "-", 
        "--quiet", "--no-warnings", "--nocheck-certificate",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        request.url
    ]

    if request.quality == 'audio':
        cmd.extend(["--extract-audio", "--audio-format", "mp3"])
    else:
        # Force MP4 merge
        cmd.extend(["--format", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"])

    # 3. Process Start
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**7)

    def iterfile():
        try:
            while True:
                chunk = proc.stdout.read(64 * 1024)
                if not chunk: break
                yield chunk
        finally:
            proc.kill()

    headers = {
        'Content-Disposition': f'attachment; filename="{encoded_filename}"',
        'Content-Type': 'audio/mpeg' if request.quality == 'audio' else 'video/mp4'
    }

    return StreamingResponse(iterfile(), headers=headers)
