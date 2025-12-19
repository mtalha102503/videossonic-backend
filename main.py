from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import yt_dlp
import aiohttp
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HELPER: GET DIRECT URL WITH HEADERS ---
def get_direct_url(video_url, quality):
    # TikTok/FB ke liye specific User-Agent zaroori hai
    ydl_opts = {
        'quiet': True,
        'format': 'best[ext=mp4]/best', # Best MP4 format
        'noplaylist': True,
        'geo_bypass': True,
        # Ye naye options TikTok error fix karenge:
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'referer': 'https://www.tiktok.com/',
    }
    
    # Audio ke liye format change
    if quality == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
    elif quality == 'low':
        ydl_opts['format'] = 'worst[ext=mp4]'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        
        # HUMEIN SIRF URL NAHI, HEADERS BHI CHAHIYE (CRITICAL FIX)
        return {
            "url": info.get('url'),
            "title": info.get('title'),
            "ext": info.get('ext'),
            "http_headers": info.get('http_headers', {}) # TikTok ke secret headers
        }

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

@app.get("/stream-video")
async def stream_video(url: str, quality: str = "medium"):
    try:
        # 1. Video Info Nikalo
        data = get_direct_url(url, quality)
        direct_url = data['url']
        headers = data['http_headers'] # Ye TikTok ke liye zaroori hai
        
        if not direct_url:
            raise HTTPException(status_code=404, detail="No URL found")

        # 2. Async Client (Isme Headers pass karna lazmi hai)
        async def iterfile():
            async with aiohttp.ClientSession() as session:
                # IMPORTANT: yaha 'headers=headers' pass kiya hai
                async with session.get(direct_url, headers=headers) as resp:
                    
                    # Pehle check karo ke TikTok ne 200 OK bola ya nahi
                    if resp.status != 200:
                        print(f"Error from CDN: {resp.status}")
                        # Agar error hai to ye generator khatam ho jayega
                        # User ko corrupt file nahi milegi, connection close ho jayega
                        return 

                    async for chunk in resp.content.iter_chunked(1024 * 1024):
                        yield chunk

        # 3. Filename Clean karo
        clean_title = "".join(c for c in data['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{clean_title}.{data['ext']}"
        
        return StreamingResponse(
            iterfile(),
            media_type="application/octet-stream",
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        print(f"Server Error: {str(e)}")
        return {"status": "error", "message": str(e)}
