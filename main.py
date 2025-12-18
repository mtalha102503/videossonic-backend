from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import yt_dlp
import urllib.parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Info Route (Ye same rahega)
@app.post("/get-info")
async def get_info(data: dict):
    url = data.get("url")
    ydl_opts = {'quiet': True, 'nocheckcertificate': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "status": "success",
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail'),
                "platform": info.get('extractor_key')
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 🔥 UNIVERSAL DOWNLOADER (NO REDIRECTS - ONLY STREAM) 🔥 ---
@app.get("/download")
async def download_video(url: str = Query(...), quality: str = Query("1080")):
    
    # 1. Title Fetch Karo
    video_title = "VideosSonic_Video"
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'nocheckcertificate': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            # Title clean karo
            video_title = info.get('title', 'video').replace('"', '').replace("'", "").replace(" ", "_")
    except:
        pass

    # 2. Filename Encoding
    ext = "mp3" if quality == 'audio' else "mp4"
    encoded_filename = urllib.parse.quote(f"{video_title[:50]}.{ext}")

    # 3. Command Construction (FFMPEG Pipeline)
    # Ab HAR platform is process se guzrega. 
    cmd = [
        "yt-dlp",
        "--output", "-",  # Output to Pipe
        "--quiet", "--no-warnings", 
        "--nocheck-certificate",
        # TikTok ke liye User-Agent bohot zaroori hai
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        url
    ]

    if quality == 'audio':
        cmd.extend(["--extract-audio", "--audio-format", "mp3"])
    else:
        # Har video ko force karo ke wo MP4 bane
        cmd.extend(["--format", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"])

    # 4. Stream Start
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**7)

    def iterfile():
        try:
            while True:
                chunk = proc.stdout.read(64 * 1024)
                if not chunk: break
                yield chunk
        finally:
            proc.kill()

    headers = {
        'Content-Disposition': f'attachment; filename="{encoded_filename}"',
        'Content-Type': 'audio/mpeg' if quality == 'audio' else 'video/mp4'
    }

    return StreamingResponse(iterfile(), headers=headers)
