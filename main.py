from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
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

# --- ZAROORI: YE WALA CODE HONA CHAHIYE ---
@app.get("/download")
async def download_video(url: str = Query(...), quality: str = Query("1080")):
    
    # 1. URL Check
    url_lower = url.lower()
    
    # === TIKTOK & FACEBOOK (FAST REDIRECT) ===
    if "tiktok" in url_lower or "facebook" in url_lower or "fb.watch" in url_lower:
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'nocheckcertificate': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                # Ye browser ko bhejega asli link par
                return RedirectResponse(url=info.get('url'))
        except:
            pass 

    # === AMAZON & INSTAGRAM (STREAMING) ===
    video_title = "VideosSonic_Video"
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'video').replace('"', '').replace("'", "").replace(" ", "_")
    except:
        pass

    encoded_filename = urllib.parse.quote(f"{video_title[:50]}.mp4")
    if quality == 'audio':
        encoded_filename = urllib.parse.quote(f"{video_title[:50]}.mp3")

    # Command
    cmd = [
        "yt-dlp", "--output", "-", "--quiet", "--no-warnings", 
        "--nocheck-certificate", url
    ]

    if quality == 'audio':
        cmd.extend(["--extract-audio", "--audio-format", "mp3"])
    else:
        cmd.extend(["--format", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"])

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

# Info Route (Ye bhi zaroori hai)
@app.post("/get-info")
async def get_info(data: dict):
    url = data.get("url")
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "status": "success",
            "title": info.get('title'),
            "thumbnail": info.get('thumbnail')
        }
