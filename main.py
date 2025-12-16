from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import time
import glob
import random

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
    quality: str = "best"

# --- FAKE IPHONE HEADERS ---
# Ye headers Instagram ko dhoka denge
IPHONE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'TE': 'trailers'
}

@app.post("/get-info")
async def get_info(request: DownloadRequest):
    cookie_file = 'cookies.txt' if os.path.exists('cookies.txt') else None
    
    ydl_opts = {
        'quiet': True,
        'nocheckcertificate': True,
        'cookiefile': cookie_file,
        'http_headers': IPHONE_HEADERS, # <--- IPHONE HEADERS
        'extractor_args': {
            'instagram': {
                'max_comments': ['0'] # Comments mat lao, fast chalega
            }
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
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=200)

@app.post("/download-video")
async def download_video(request: DownloadRequest):
    try:
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        files = glob.glob('downloads/*')
        for f in files:
            try: os.remove(f)
            except: pass

        timestamp = int(time.time())
        q = str(request.quality)
        
        # --- QUALITY LOGIC ---
        postprocessors = []
        format_str = 'bestvideo+bestaudio/best'
        output_path = f"downloads/%(title)s_Video_{timestamp}.%(ext)s"

        if q == 'audio':
            format_str = 'bestaudio/best'
            output_path = f"downloads/%(title)s_Audio_{timestamp}.%(ext)s"
            postprocessors = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',}]
        elif q in ['360', '480', '720', '1080']:
            format_str = f'bestvideo[height<={q}]+bestaudio/best[height<={q}]/bestvideo+bestaudio/best'
            output_path = f"downloads/%(title)s_{q}p_{timestamp}.%(ext)s"
        
        cookie_file = 'cookies.txt' if os.path.exists('cookies.txt') else None

        ydl_opts = {
            'outtmpl': output_path,
            'format': format_str,
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': True,
            'postprocessors': postprocessors,
            'proxy': 'http://127.0.0.1:8118',
            'cookiefile': cookie_file,
            'http_headers': IPHONE_HEADERS, # <--- IPHONE HEADERS
        }

        # STEP 2: DOWNLOAD
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])

        # STEP 3: FIND FILE
        list_of_files = glob.glob('downloads/*') 
        if not list_of_files:
             return JSONResponse(content={"status": "error", "message": "Download failed. Instagram Rate Limit."}, status_code=200)
        
        final_file = max(list_of_files, key=os.path.getctime)
        
        return FileResponse(path=final_file, filename=os.path.basename(final_file), media_type='application/octet-stream')

    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

