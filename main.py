from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import requests
import urllib.parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InfoRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    quality: str  # '1080', '720', '360', 'audio'

# 1. Sirf Info lane ke liye API (Ye waisa hi rahega)
@app.post("/get-info")
async def get_info(request: InfoRequest):
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

# 2. FAST STREAMING DOWNLOAD API (Magic Here ⚡)
@app.post("/download-video")
async def download_video(request: DownloadRequest):
    # Quality Mapping
    format_str = 'best' # Default
    
    if request.quality == 'audio':
        format_str = 'bestaudio/best'
    elif request.quality == '1080':
        format_str = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
    elif request.quality == '720':
        format_str = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
    elif request.quality == '480':
        format_str = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
    elif request.quality == '360':
        format_str = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best'

    ydl_opts = {
        'format': format_str,
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Video Info nikalo (Download nahi karna)
            info = ydl.extract_info(request.url, download=False)
            
            # 2. Direct URL pakdo
            direct_url = info.get('url')
            
            # Filename Clean karo
            title = info.get('title', 'video').replace('"', '').replace("'", "")
            encoded_filename = urllib.parse.quote(f"{title}.mp4") # Safe filename
            
            # Agar audio maanga hai to extension change
            if request.quality == 'audio':
                encoded_filename = urllib.parse.quote(f"{title}.mp3")

            # 3. Connection banao (Server to TikTok/Amazon)
            # stream=True bohot zaroori hai
            external_req = requests.get(direct_url, stream=True, headers=info.get('http_headers'))

            # 4. Generator Function (Chunk by Chunk data bhejega)
            def iterfile():
                try:
                    for chunk in external_req.iter_content(chunk_size=1024 * 1024): # 1MB Chunks
                        if chunk:
                            yield chunk
                except Exception as e:
                    print(f"Stream Error: {e}")

            # 5. Headers set karo taaki browser ko lage file aa rahi hai
            headers = {
                'Content-Disposition': f'attachment; filename="{encoded_filename}"',
                'Content-Type': external_req.headers.get('content-type', 'video/mp4')
            }
            
            # Agar file size pata hai to bhej do (Progress bar ke liye)
            if 'content-length' in external_req.headers:
                headers['Content-Length'] = external_req.headers['content-length']

            # 6. Response Bhejo (Direct Stream)
            return StreamingResponse(
                iterfile(),
                headers=headers,
                media_type=external_req.headers.get('content-type', 'video/mp4')
            )

    except Exception as e:
        print(f"Server Error: {str(e)}")
        # Agar error aaye to JSON return karo (Frontend handle karega)
        return {"status": "error", "message": str(e)}
