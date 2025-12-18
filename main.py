from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import uuid
import time

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

# --- CLEANUP FUNCTION (File bhejne ke baad delete karega) ---
def cleanup_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
            print(f"Deleted temp file: {path}")
    except Exception as e:
        print(f"Error deleting file: {e}")

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

# --- 🔥 THE STABLE DOWNLOADER (TEMP FILE METHOD) 🔥 ---
@app.post("/download-video")
async def download_video(request: RequestModel, background_tasks: BackgroundTasks):
    
    # 1. Unique Filename banao (Taaki mix na ho)
    file_id = str(uuid.uuid4())
    filename = f"video_{file_id}.mp4"
    if request.quality == 'audio':
        filename = f"audio_{file_id}.mp3"
    
    # 2. Options Setup
    ydl_opts = {
        'outtmpl': filename, # Temp name
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # Agar Amazon/TikTok HLS hai to ye usse MP4 bana dega
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
        'overwrites': True,
    }

    if request.quality == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]

    try:
        # 3. Server par Download Start
        print(f"Downloading to server: {filename}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])

        # 4. Audio fix (yt-dlp kabhi kabhi .mp3 add kar deta hai extension mein)
        final_path = filename
        if request.quality == 'audio' and not os.path.exists(final_path):
            if os.path.exists(filename + ".mp3"):
                final_path = filename + ".mp3"

        # 5. --- CRITICAL CHECK: File Size ---
        if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
            raise Exception("Download failed (0 bytes). Server Blocked or FFMPEG missing.")

        # 6. User ko Bhejo aur baad mein Delete karo
        # Browser ko asli naam batane ke liye
        download_name = f"VideosSonic_{int(time.time())}.{'mp3' if request.quality == 'audio' else 'mp4'}"
        
        background_tasks.add_task(cleanup_file, final_path)
        
        return FileResponse(
            path=final_path, 
            filename=download_name, 
            media_type='application/octet-stream'
        )

    except Exception as e:
        # Agar error aaye to bhi safai karo
        if os.path.exists(filename):
            os.remove(filename)
        print(f"Error: {e}")
        return {"status": "error", "message": f"Server processing failed: {str(e)}"}
