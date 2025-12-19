from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import yt_dlp
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HELPER FUNCTION TO GET DIRECT URL ---
def get_direct_url(video_url, quality):
    # 'best' format wo hota hai jisme Audio+Video dono hon (usually 720p/360p)
    # Agar alag alag streams uthayenge to merge krna padega jo slow hai.
    format_selection = 'best[ext=mp4]/best'
    
    if quality == 'low':
        format_selection = 'worst[ext=mp4]/worst'
    elif quality == 'audio':
        format_selection = 'bestaudio/best'

    ydl_opts = {
        'quiet': True,
        'format': format_selection,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info.get('url'), info.get('title'), info.get('ext')

# 1. Info API (Ye wahi purani wali hai)
@app.post("/get-info")
async def get_info(request: dict):
    url = request.get("url")
    ydl_opts = {'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "status": "success",
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "platform": info.get('extractor_key')
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 2. STREAM DOWNLOAD API (GET Request for Browser)
# Note: Hum POST ki jagah GET use karenge taake browser direct download handle kare
@app.get("/stream-video")
async def stream_video(url: str, quality: str = "medium"):
    try:
        # 1. Direct YouTube/Server URL nikalo
        direct_url, title, ext = get_direct_url(url, quality)
        
        if not direct_url:
            raise HTTPException(status_code=404, detail="Could not extract video URL")

        # 2. External Server se connection banao (Stream=True)
        # Ye Render server ko bridge banata hai
        external_req = requests.get(direct_url, stream=True)

        # 3. Generator function jo data tukdo me bhejega
        def iterfile():
            try:
                for chunk in external_req.iter_content(chunk_size=1024 * 1024): # 1MB Chunks
                    if chunk:
                        yield chunk
            except Exception as e:
                print(f"Stream Error: {e}")

        # 4. Headers set karo taake browser ko lage ye file download ho rahi hai
        clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{clean_title}.{ext}"
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }

        return StreamingResponse(
            iterfile(),
            media_type=external_req.headers.get("content-type"),
            headers=headers
        )

    except Exception as e:
        return {"status": "error", "message": str(e)}
