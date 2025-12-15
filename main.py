from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import time
import glob

app = FastAPI()

# 1. CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Data Model
class DownloadRequest(BaseModel):
    url: str
    quality: str = "best" # Default value

# 3. Get Info Route
@app.post("/get-info")
async def get_info(request: DownloadRequest):
    cookie_file = 'cookies.txt' if os.path.exists('cookies.txt') else None
    
    ydl_opts = {
        'quiet': True,
        'nocheckcertificate': True,
        'cookiefile': cookie_file,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            return {
                "status": "success",
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0)
            }
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=400)

# 4. Download Route (FIXED LOGIC)
@app.post("/download-video")
async def download_video(request: DownloadRequest):
    try:
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        # Safai
        files = glob.glob('downloads/*')
        for f in files:
            try: os.remove(f)
            except: pass

        timestamp = int(time.time())
        q = str(request.quality)
        
        # --- FIXED QUALITY LOGIC ---
        # Initialize variables first to avoid errors
        postprocessors = []
        format_str = 'bestvideo+bestaudio/best' # Fallback
        output_path = f"downloads/%(title)s_Video_{timestamp}.%(ext)s"

        if q == 'audio':
            format_str = 'bestaudio/best'
            output_path = f"downloads/%(title)s_Audio_{timestamp}.%(ext)s"
            postprocessors = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',}]
        
        elif q in ['360', '480', '720', '1080']:
            # Exact resolution logic
            format_str = f'bestvideo[height<={q}]+bestaudio/best[height<={q}]'
            output_path = f"downloads/%(title)s_{q}p_{timestamp}.%(ext)s"
        
        # Cookies check
        cookie_file = 'cookies.txt' if os.path.exists('cookies.txt') else None

        ydl_opts = {
            'outtmpl': output_path,
            'format': format_str,
            'merge_output_format': 'mp4', # Ensure MP4 for videos
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'postprocessors': postprocessors,
            'cookiefile': cookie_file,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
        }

        filename = ""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info)
            
            # MP3 Extension Fix
            if q == 'audio':
                base, _ = os.path.splitext(filename)
                filename = base + ".mp3"
            # MP4 Extension Fix (If merged)
            elif q != 'audio' and not filename.endswith('.mp4'):
                 base, _ = os.path.splitext(filename)
                 if os.path.exists(base + ".mp4"):
                     filename = base + ".mp4"

        # Verification
        if not filename or not os.path.exists(filename):
             return JSONResponse(content={"status": "error", "message": "Download failed. Format not available."}, status_code=500)

        return FileResponse(path=filename, filename=os.path.basename(filename), media_type='application/octet-stream')

    except Exception as e:
        print(f"Server Error: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
