from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

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

@app.post("/get-info")
async def get_info(request: RequestModel):
    # Sirf info laane ke liye settings
    ydl_opts = {
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
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

# --- 🔥 MAIN MAGIC: GET DIRECT LINK (NO SERVER DOWNLOAD) 🔥 ---
@app.post("/download-video")
async def get_direct_link(request: RequestModel):
    
    # Quality select karne ki logic
    format_selection = 'best'
    if request.quality == 'audio':
        format_selection = 'bestaudio/best'
    elif request.quality == '1080':
        format_selection = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
    
    ydl_opts = {
        'format': format_selection,
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Info extract karo
            info = ydl.extract_info(request.url, download=False)
            
            # 2. Asli Direct URL nikalo (Amazon/TikTok server ka link)
            direct_url = info.get('url')
            
            # Title bhi bhej do taaki filename sahi ban sake
            title = info.get('title', 'video').replace('"', '').replace("'", "")
            
            return {
                "status": "success",
                "direct_url": direct_url,
                "filename": f"{title}.mp4"
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}
