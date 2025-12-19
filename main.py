from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import yt_dlp
import aiohttp # Ye nayi library hai
import urllib.parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HELPER: GET DIRECT URL ---
def get_direct_url(video_url, quality):
    # Format selection: Best file with Audio+Video combined
    format_selection = 'best[ext=mp4]/best'
    
    if quality == 'low':
        format_selection = 'worst[ext=mp4]/worst'
    elif quality == 'audio':
        format_selection = 'bestaudio/best'

    ydl_opts = {
        'quiet': True,
        'format': format_selection,
        'noplaylist': True,
        'geo_bypass': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info.get('url'), info.get('title'), info.get('ext')

# 1. INFO API
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

# 2. STREAM DOWNLOAD API (FIXED WITH AIOHTTP)
@app.get("/stream-video")
async def stream_video(url: str, quality: str = "medium"):
    try:
        # 1. URL Nikalo
        direct_url, title, ext = get_direct_url(url, quality)
        
        if not direct_url:
            raise HTTPException(status_code=404, detail="Could not extract video URL")

        # 2. Async Client Session start karo
        # Ye 'async' hai, to server block nahi hoga
        async def iterfile():
            async with aiohttp.ClientSession() as session:
                async with session.get(direct_url) as resp:
                    # Video data ko chote tukdo (chunks) me user ko bhejo
                    async for chunk in resp.content.iter_chunked(1024 * 1024): # 1MB chunks
                        yield chunk

        # 3. Filename set karo
        clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{clean_title}.{ext}"
        
        # NOTE: Content-Disposition attachment browser ko force karta hai download ke liye
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }

        # 4. Return StreamingResponse
        # Hum headers me 'media_type' nahi de rahe taki browser khud detect kare
        # ya generic octet-stream use kare taake play hone ki bajaye download ho.
        return StreamingResponse(
            iterfile(),
            media_type="application/octet-stream", 
            headers=headers
        )

    except Exception as e:
        # Agar start me hi error aaye to JSON return karo
        return {"status": "error", "message": str(e)}
