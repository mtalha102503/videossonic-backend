from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import time
import glob

app = FastAPI()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    quality: str = "1080" # Default value

@app.post("/get-info")
async def get_info(request: DownloadRequest):
    # Cookie check
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
                "title": info.get('title', 'Unknown Title'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0)
            }
    except Exception as e:
        print(f"Info Error: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=400)

@app.post("/download-video")
async def download_video(request: DownloadRequest):
    try:
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        # Purani files safai (Cleanup)
        files = glob.glob('downloads/*')
        for f in files:
            try: os.remove(f)
            except: pass

        timestamp = int(time.time())
        q = str(request.quality) # Ensure string
        
        # --- ROBUST QUALITY LOGIC ---
        postprocessors = []
        format_str = 'bestvideo+bestaudio/best' # Default fallback
        
        if q == 'audio':
            format_str = 'bestaudio/best'
            output_path = f"downloads/%(title)s_Audio_{timestamp}.%(ext)s"
            postprocessors = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',}]
        elif q == '360':
            format_str = 'bestvideo[height<=360]+bestaudio/best[height<=360]'
            output_path = f"downloads/%(title)s_360p_{timestamp}.%(ext)s"
        elif q == '480':
            format_str = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
            output_path = f"downloads/%(title)s_480p_{timestamp}.%(ext)s"
        elif q == '720':
            format_str = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
            output_path = f"downloads/%(title)s_720p_{timestamp}.%(ext)s"
        elif q == '1080':
            format_str = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
            output_path = f"downloads/%(title)s_1080p_{timestamp}.%(ext)s"
        else: 
            # Default High
            output_path = f"downloads/%(title)s_HD_{timestamp}.%(ext)s"

        # Cookies check
        cookie_file = 'cookies.txt' if os.path.exists('cookies.txt') else None

        ydl_opts = {
            'outtmpl': output_path,
            'format': format_str,
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
            
            # Handle MP3 Extension Change
            if q == 'audio':
                base, _ = os.path.splitext(filename)
                filename = base + ".mp3"

        if not filename or not os.path.exists(filename):
             print("Error: File not found after download.")
             return JSONResponse(content={"status": "error", "message": "Download failed. Please try again."}, status_code=500)

        return FileResponse(path=filename, filename=os.path.basename(filename), media_type='application/octet-stream')

    except Exception as e:
        print(f"Download Error: {str(e)}")
        return JSONResponse(content={"status": "error", "message": f"Server Error: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
