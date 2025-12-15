from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import time
import glob

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    quality: str = "medium"

@app.post("/get-info")
async def get_info(request: DownloadRequest):
    # Agar cookies file hai to use karo
    cookie_file = 'cookies.txt' if os.path.exists('cookies.txt') else None
    
    ydl_opts = {
        'quiet': True,
        'nocheckcertificate': True,
        'cookiefile': cookie_file,  # <--- YAHAN HAI JADU 🍪
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            return {
                "status": "success",
                "title": info.get('title', 'Unknown Title'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0)
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/download-video")
async def download_video(request: DownloadRequest):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # Safai
    files = glob.glob('downloads/*')
    for f in files:
        try: os.remove(f)
        except: pass

    timestamp = int(time.time())
    
    # Quality logic
    if request.quality == 'audio':
        format_str = 'bestaudio/best'
        output_path = f"downloads/%(title)s_Audio_{timestamp}.%(ext)s"
        postprocessors = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',}]
    else: 
        format_str = 'bestvideo+bestaudio/best'
        output_path = f"downloads/%(title)s_Video_{timestamp}.%(ext)s"
        postprocessors = []

    # Cookies check
    cookie_file = 'cookies.txt' if os.path.exists('cookies.txt') else None

    ydl_opts = {
        'outtmpl': output_path,
        'format': format_str,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'cookiefile': cookie_file,  # <--- COOKIES ENABLED 🍪
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }

    try:
        filename = ""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info)
            if request.quality == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

        if not filename or not os.path.exists(filename):
             return {"status": "error", "message": "Download failed. Still blocked by YouTube."}

        return FileResponse(path=filename, filename=os.path.basename(filename), media_type='application/octet-stream')

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
