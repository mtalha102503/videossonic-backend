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

class InfoRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    quality: str

# 1. Info API (Same as before)
@app.post("/get-info")
async def get_info(request: InfoRequest):
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

# 2. SMART PIPELINE DOWNLOAD API (Ye hai Magic Code 🪄)
@app.post("/download-video")
async def download_video(request: DownloadRequest):
    
    # Filename clean karo taaki download popup mein sahi dikhe
    # Hum pehle info fetch karenge sirf title ke liye (Lightweight)
    video_title = "VideosSonic_Video"
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(request.url, download=False)
            video_title = info.get('title', 'video').replace('"', '').replace("'", "")
    except:
        pass

    encoded_filename = urllib.parse.quote(f"{video_title}.mp4")

    # Command banao: yt-dlp data ko seedha "STDOUT" (Pipe) mein fekega
    cmd = [
        "yt-dlp",
        "--output", "-",           # '-' ka matlab hai: Disk par mat likho, Pipe karo
        "--quiet",                 # Shor mat machao
        "--no-warnings",
        "--nocheck-certificate",   # SSL errors ignore karo
        "--format", "best[ext=mp4]/best", # Best MP4 dhoondo
        request.url
    ]

    # Agar Audio chahiye to command change
    if request.quality == 'audio':
        cmd = [
            "yt-dlp",
            "--output", "-",
            "--quiet",
            "--no-warnings",
            "--extract-audio",
            "--audio-format", "mp3",
            request.url
        ]
        encoded_filename = urllib.parse.quote(f"{video_title}.mp3")

    # Subprocess start karo
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Ye Generator function chunk-by-chunk data bhejega
    def iterfile():
        try:
            while True:
                # 64KB chunks padho
                chunk = proc.stdout.read(64 * 1024)
                if not chunk:
                    break
                yield chunk
        except Exception as e:
            print(f"Streaming Error: {e}")
            proc.kill()
        finally:
            proc.kill() # Safai zaroori hai

    # Headers set karo
    headers = {
        'Content-Disposition': f'attachment; filename="{encoded_filename}"'
    }

    return StreamingResponse(iterfile(), media_type="video/mp4", headers=headers)
