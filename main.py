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
    ydl_opts = {
        'quiet': True,
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
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

    # Purani files safai
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

    # --- ANDROID MODE SETTINGS ---
    ydl_opts = {
        'outtmpl': output_path,
        'format': format_str,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'source_address': '0.0.0.0', # Force IPv4
        
        # JADU YAHAN HAI (YouTube ko lagega ye Mobile App hai):
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
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
             return {"status": "error", "message": "Download failed. YouTube is blocking Cloud IPs."}

        return FileResponse(path=filename, filename=os.path.basename(filename), media_type='application/octet-stream')

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
