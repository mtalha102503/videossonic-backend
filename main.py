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
        # Return 200 so frontend can display the error message
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=200)

# 4. Download Route (DEBUG MODE ENABLED 🛠️)
@app.post("/download-video")
async def download_video(request: DownloadRequest):
    try:
        # Folder Check
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        # STEP 1: SAFAI (Folder khali karo)
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
            format_str = f'bestvideo[height<={q}]+bestaudio/best[height<={q}]'
            output_path = f"downloads/%(title)s_{q}p_{timestamp}.%(ext)s"
        
        # Check Cookies explicitly
        if os.path.exists('cookies.txt'):
            cookie_file = 'cookies.txt'
            print("🍪 Cookies Found & Loaded") 
        else:
            cookie_file = None
            print("⚠️ No Cookies Found")

        ydl_opts = {
            'outtmpl': output_path,
            'format': format_str,
            'merge_output_format': 'mp4', # Force MP4
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False, # Keep False to catch real errors
            'logtostderr': True,
            'postprocessors': postprocessors,
            'cookiefile': cookie_file,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
        }

        # STEP 2: DOWNLOAD
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])

        # STEP 3: FIND FILE
        time.sleep(0.5) # Wait for file system
        list_of_files = glob.glob('downloads/*') 
        
        if not list_of_files:
             # Agar yahan pohnche, matlab yt-dlp fail nahi hua par file bhi nahi bani
             return JSONResponse(content={"status": "error", "message": "Download failed. Server IP might be blocked or format unavailable."}, status_code=200)
        
        final_file = max(list_of_files, key=os.path.getctime)
        
        return FileResponse(path=final_file, filename=os.path.basename(final_file), media_type='application/octet-stream')

    except Exception as e:
        # Ab Asal Error Frontend Par Jayega (Status 200 ke sath)
        print(f"Server Error Details: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
