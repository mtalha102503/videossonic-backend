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

# --- SMART AGENT ROTATION ---
USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
]

def get_random_header():
    return {'User-Agent': random.choice(USER_AGENTS)}

@app.post("/get-info")
async def get_info(request: DownloadRequest):
    cookie_file = 'cookies.txt' if os.path.exists('cookies.txt') else None
    
    ydl_opts = {
        'quiet': True,
        'nocheckcertificate': True,
        'cookiefile': cookie_file,
        'http_headers': get_random_header(),
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

        # Safai
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

        # --- AUTO-RETRY SYSTEM (User ko error nahi dikhega) ---
        max_retries = 3
        final_file = None
        last_error = ""

        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1} of {max_retries}...")
                
                # Har baar naya bhesh (New Headers)
                current_headers = get_random_header()
                
                extractor_args = {}
                if 'facebook.com' in request.url or 'fb.watch' in request.url:
                     extractor_args = {'facebook': {'player_client': ['android']}}

                ydl_opts = {
                    'outtmpl': output_path,
                    'format': format_str,
                    'merge_output_format': 'mp4',
                    'noplaylist': True,
                    'nocheckcertificate': True,
                    'ignoreerrors': True,
                    'logtostderr': True,
                    'postprocessors': postprocessors,
                    'cookiefile': cookie_file,
                    'http_headers': current_headers,
                    'extractor_args': extractor_args
                }

                # Download Try Karein
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([request.url])

                # Check karein file aayi ya nahi
                list_of_files = glob.glob('downloads/*') 
                if list_of_files:
                    # File mil gayi! Loop todo aur user ko bhejo
                    final_file = max(list_of_files, key=os.path.getctime)
                    if os.path.getsize(final_file) > 1000: # Verify size
                        break 
                
                # Agar file nahi mili, to thoda saans lo aur dobara try karo
                time.sleep(1)

            except Exception as e:
                print(f"Retry failed: {str(e)}")
                last_error = str(e)
                time.sleep(1)

        # Agar 3 koshishon ke baad bhi kuch na mile
        if not final_file or not os.path.exists(final_file):
             return JSONResponse(content={"status": "error", "message": "Download failed after multiple attempts. Server Blocked."}, status_code=200)
        
        return FileResponse(path=final_file, filename=os.path.basename(final_file), media_type='application/octet-stream')

    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
