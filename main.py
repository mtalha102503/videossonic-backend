from fastapi.responses import FileResponse
import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

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
    quality: str  # 'high', 'medium', 'low', 'audio'

# 1. Sirf Info lane ke liye API
@app.post("/get-info")
async def get_info(request: InfoRequest):
    ydl_opts = {'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            return {
                "status": "success",
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "platform": info.get('extractor_key')
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 2. Asal Download ke liye API
# Is function ko replace karein
@app.post("/download-video")
async def download_video(request: DownloadRequest):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    timestamp = int(time.time())
    
    # Quality Settings (Wahi purani wali)
    if request.quality == 'audio':
        format_str = 'bestaudio/best'
        output_path = f"downloads/%(title).50s_Audio_{timestamp}.%(ext)s"
        postprocessors = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',}]
    elif request.quality == 'low':
        format_str = 'worstvideo[height>=360]+worstaudio/worst[height>=360]'
        output_path = f"downloads/%(title).50s_Low_{timestamp}.%(ext)s"
        postprocessors = []
    elif request.quality == 'medium':
        format_str = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        output_path = f"downloads/%(title).50s_Medium_{timestamp}.%(ext)s"
        postprocessors = []
    else: 
        format_str = 'bestvideo+bestaudio/best'
        output_path = f"downloads/%(title).50s_High_{timestamp}.%(ext)s"
        postprocessors = []

    # --- UPDATE: RETRY LOGIC ADDED HERE ---
    ydl_opts = {
        'outtmpl': output_path,
        'format': format_str,
        'quiet': False,
        'noplaylist': True,
        'updatetime': False,
        'postprocessors': postprocessors,
        'source_address': '0.0.0.0',
        
        # Ye nayi lines hain jo error rokengi:
        'retries': 10,              # Agar fail ho to 10 baar try karo
        'fragment_retries': 10,     # Agar video ka tukda fail ho to retry karo
        'socket_timeout': 30,       # 30 second tak wait karo
        'ignoreerrors': True        # Choti moti errors ko ignore karo
    }

    try:
        print(f"Downloading {request.quality} quality...")
        filename = ""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info)
            
            if request.quality == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

        # Check karein ke file bani bhi hai ya nahi (Retry ke baad)
        if not filename or not os.path.exists(filename):
             return {"status": "error", "message": "Download failed after retries. Internet unstable?"}

        return FileResponse(path=filename, filename=os.path.basename(filename), media_type='application/octet-stream')

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"status": "error", "message": str(e)}

