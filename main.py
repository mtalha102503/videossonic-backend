from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import time
import glob

app = FastAPI()

# CORS Setup (Mobile/Browser connection ke liye)
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
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        # Fake Browser Headers (YouTube ko dhoka dene ke liye)
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
    # Downloads folder check
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # Purani files delete karein (Server clean rakhne ke liye)
    files = glob.glob('downloads/*')
    for f in files:
        try:
            os.remove(f)
        except:
            pass

    timestamp = int(time.time())
    
    # Quality Settings
    if request.quality == 'audio':
        format_str = 'bestaudio/best'
        output_path = f"downloads/%(title)s_Audio_{timestamp}.%(ext)s"
        postprocessors = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',}]
    elif request.quality == 'low':
        format_str = 'worstvideo[height>=360]+worstaudio/worst[height>=360]'
        output_path = f"downloads/%(title)s_Low_{timestamp}.%(ext)s"
        postprocessors = []
    elif request.quality == 'medium':
        format_str = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        output_path = f"downloads/%(title)s_Medium_{timestamp}.%(ext)s"
        postprocessors = []
    else: 
        format_str = 'bestvideo+bestaudio/best'
        output_path = f"downloads/%(title)s_High_{timestamp}.%(ext)s"
        postprocessors = []

    # --- MAIN SETTINGS FOR YOUTUBE ---
    ydl_opts = {
        'outtmpl': output_path,
        'format': format_str,
        'noplaylist': True,
        'postprocessors': postprocessors,
        'quiet': False,
        'no_warnings': True,
        'nocheckcertificate': True, # Certificate errors ignore karo
        'ignoreerrors': True,       # Choti moti errors ignore karo
        
        # Ye sabse zaroori hai (Fake Identity):
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
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
             return {"status": "error", "message": "Download failed. Try again."}

        # Mobile ko file bhejo
        return FileResponse(path=filename, filename=os.path.basename(filename), media_type='application/octet-stream')

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
