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
    quality: str = "best"

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

# 4. Download Route (NUCLEAR FIX ☢️)
@app.post("/download-video")
async def download_video(request: DownloadRequest):
    try:
        # Folder Check
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        # STEP 1: SAFAI (Folder khali karo)
        # Isse confirm ho jayega ke jo file bachegi wo HAMARI hai.
        files = glob.glob('downloads/*')
        for f in files:
            try: os.remove(f)
            except: pass

        timestamp = int(time.time())
        q = str(request.quality)
        
        # --- QUALITY LOGIC ---
        postprocessors = []
        format_str = 'bestvideo+bestaudio/best' # Default
        output_path = f"downloads/%(title)s_Video_{timestamp}.%(ext)s"

        if q == 'audio':
            format_str = 'bestaudio/best'
            output_path = f"downloads/%(title)s_Audio_{timestamp}.%(ext)s"
            postprocessors = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',}]
        
        elif q in ['360', '480', '720', '1080']:
            # Koshish karo specific height mile, warna best le lo
            format_str = f'bestvideo[height<={q}]+bestaudio/best[height<={q}]'
            output_path = f"downloads/%(title)s_{q}p_{timestamp}.%(ext)s"
        
        cookie_file = 'cookies.txt' if os.path.exists('cookies.txt') else None

        ydl_opts = {
            'outtmpl': output_path,
            'format': format_str,
            'merge_output_format': 'mp4', # Force MP4
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'postprocessors': postprocessors,
            'cookiefile': cookie_file,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
        }

        # STEP 2: DOWNLOAD
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])

        # STEP 3: FIND FILE (The Genius Part 🧠)
        # Naam guess karne ke bajaye, hum folder check karenge
        list_of_files = glob.glob('downloads/*') 
        
        if not list_of_files:
             return JSONResponse(content={"status": "error", "message": "Download failed. No file found."}, status_code=500)
        
        # Jo bhi file mili, wahi hamari hero hai
        final_file = max(list_of_files, key=os.path.getctime)
        
        return FileResponse(path=final_file, filename=os.path.basename(final_file), media_type='application/octet-stream')

    except Exception as e:
        print(f"Server Error: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
