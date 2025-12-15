from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import time
import glob

app = FastAPI()

# CORS Setup (Browser Connection)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    quality: str = "1080" # Default

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
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=400)

@app.post("/download-video")
async def download_video(request: DownloadRequest):
    # 1. Folder Check
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # 2. Cleanup (Purani files delete)
    try:
        files = glob.glob('downloads/*')
        for f in files:
            os.remove(f)
    except:
        pass

    timestamp = int(time.time())
    q = str(request.quality)
    
    # 3. Quality Settings (Simplified Logic)
    postprocessors = []
    
    # Default Format (Best Quality)
    format_str = 'bestvideo+bestaudio/best'
    output_path = f"downloads/%(title)s_HD_{timestamp}.%(ext)s"

    if q == 'audio':
        format_str = 'bestaudio/best'
        output_path = f"downloads/%(title)s_Audio_{timestamp}.%(ext)s"
        postprocessors = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',}]
    
    elif q in ['360', '480', '720', '1080']:
        # Resolution logic: Try to get specific height, fallback to best if not available
        format_str = f'bestvideo[height<={q}]+bestaudio/best[height<={q}]'
        output_path = f"downloads/%(title)s_{q}p_{timestamp}.%(ext)s"

    # 4. Cookies Check
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

    try:
        filename = ""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Agar MP3 hai to extension change karo
            if q == 'audio':
                base, _ = os.path.splitext(filename)
                filename = base + ".mp3"

        # 5. File Verification
        if not filename or not os.path.exists(filename):
             return JSONResponse(content={"status": "error", "message": "Download failed. Please try again."}, status_code=500)

        # 6. Send File to User
        return FileResponse(path=filename, filename=os.path.basename(filename), media_type='application/octet-stream')

    except Exception as e:
        # Error handling
        print(f"Error: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
