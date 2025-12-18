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

@app.post("/get-info")
async def get_info(request: RequestModel):
    ydl_opts = {
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
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

# --- 🔥 UNIVERSAL PIPELINE (NO CORRUPTION) 🔥 ---
@app.post("/download-video")
async def download_video(request: RequestModel):
    
    # 1. Clean Title Fetch Karo
    video_title = "VideosSonic_Video"
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'nocheckcertificate': True}) as ydl:
            info = ydl.extract_info(request.url, download=False)
            # Title safai
            video_title = info.get('title', 'video').replace('"', '').replace("'", "").replace(" ", "_")
            # Limit filename length
            video_title = video_title[:50]
    except:
        pass

    # 2. Filename Encoding
    ext = "mp3" if request.quality == 'audio' else "mp4"
    encoded_filename = urllib.parse.quote(f"{video_title}.{ext}")

    # 3. yt-dlp Command Construction
    # Hum '-o -' use karenge taaki disk par save na ho, seedha pipe ho.
    cmd = [
        "yt-dlp",
        "--output", "-",  # Pipe to Stdout
        "--quiet", "--no-warnings", "--nocheck-certificate",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        request.url
    ]

    # Quality Logic
    if request.quality == 'audio':
        cmd.extend(["--extract-audio", "--audio-format", "mp3"])
    elif request.quality == '1080':
        cmd.extend(["--format", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"])
    else:
        # Default Best
        cmd.extend(["--format", "best"])

    # 4. Process Start (Stream)
    # bufsize badha diya hai taaki stream smooth ho
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**7)

    # 5. Generator Function
    def iterfile():
        try:
            while True:
                # 64KB chunks read karo
                chunk = proc.stdout.read(64 * 1024)
                if not chunk:
                    break
                yield chunk
        except Exception as e:
            print(f"Stream Error: {e}")
            proc.kill()
        finally:
            proc.kill()

    # 6. Set Headers
    headers = {
        'Content-Disposition': f'attachment; filename="{encoded_filename}"',
        'Content-Type': 'audio/mpeg' if request.quality == 'audio' else 'video/mp4'
    }

    return StreamingResponse(iterfile(), headers=headers)
