from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
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

# --- 🔥 THE HYBRID DOWNLOADER (SMART LOGIC) 🔥 ---
@app.post("/download-video")
async def download_video(request: RequestModel):
    
    # 1. URL Check: Kya ye Amazon hai?
    is_amazon = "amazon" in request.url or "amzn" in request.url
    
    # 2. Title Clean Karo (Common Step)
    video_title = "VideosSonic_Video"
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(request.url, download=False)
            video_title = info.get('title', 'video').replace('"', '').replace("'", "").replace(" ", "_")
            direct_url = info.get('url') # Direct link for non-amazon
    except:
        pass

    filename = f"{video_title[:50]}.mp4"
    if request.quality == 'audio':
        filename = f"{video_title[:50]}.mp3"
    
    encoded_filename = urllib.parse.quote(filename)

    # === CASE A: AGAR TIKTOK, INSTA, FB HAI (Direct Link Bhejo) ===
    if not is_amazon:
        # Hum JSON bhejenge taaki browser khud download kare (Fastest Speed)
        return JSONResponse(content={
            "status": "direct_link",
            "direct_url": direct_url,
            "filename": filename
        })

    # === CASE B: AGAR AMAZON HAI (Pipeline Use Karo) ===
    # Kyunki Amazon direct link browser mein play ho jata hai, download nahi hota.
    else:
        cmd = [
            "yt-dlp",
            "--output", "-",
            "--quiet", "--no-warnings", "--nocheck-certificate",
            request.url
        ]

        if request.quality == 'audio':
            cmd.extend(["--extract-audio", "--audio-format", "mp3"])
        elif request.quality == '1080':
            cmd.extend(["--format", "bestvideo[height<=1080]+bestaudio/best"])
        else:
            cmd.extend(["--format", "best"])

        # Stream Process Start
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
            'Content-Type': 'video/mp4' if request.quality != 'audio' else 'audio/mpeg'
        }
        
        # Ye response 'File' ki tarah behave karega
        return StreamingResponse(iterfile(), headers=headers)
