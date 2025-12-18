from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, RedirectResponse
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

# 1. INFO API (Metadata ke liye)
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

# --- 🔥 MASTER DOWNLOAD ENDPOINT (GET METHOD) 🔥 ---
# Frontend bas is link ko new tab mein kholega
@app.get("/download")
async def download_video(url: str = Query(...), quality: str = Query("1080")):
    
    # 1. Pehle URL analyze karo
    url_lower = url.lower()
    
    # FAST LANE: TikTok & Facebook (Redirect Mode)
    # Inke liye hum server use nahi karenge, seedha user ko bhej denge source par
    if "tiktok" in url_lower or "facebook" in url_lower or "fb.watch" in url_lower:
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'nocheckcertificate': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                # Browser ko bolo: "Jao yahan se download karlo" (307 Redirect)
                return RedirectResponse(url=info.get('url'))
        except:
            pass # Agar fail hua to neeche Stream method par gir jayega

    # SECURE LANE: Amazon & Instagram (Proxy Stream Mode)
    # Ye complex sites hain, inhein hum server ke through guzarenge
    
    # Title Fetch
    video_title = "VideosSonic_Download"
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'video').replace('"', '').replace("'", "").replace(" ", "_")
    except:
        pass

    encoded_filename = urllib.parse.quote(f"{video_title[:50]}.mp4")
    if quality == 'audio':
        encoded_filename = urllib.parse.quote(f"{video_title[:50]}.mp3")

    # Command Construction
    cmd = [
        "yt-dlp",
        "--output", "-",  # Pipe Output
        "--quiet", "--no-warnings", 
        "--nocheck-certificate",
        url
    ]

    if quality == 'audio':
        cmd.extend(["--extract-audio", "--audio-format", "mp3"])
    else:
        # Amazon HLS fix + High Quality Merge
        cmd.extend(["--format", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"])

    # Stream Start
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
        'Content-Type': 'audio/mpeg' if quality == 'audio' else 'video/mp4'
    }

    return StreamingResponse(iterfile(), headers=headers)
