from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import yt_dlp
import time

app = Flask(__name__)
CORS(app)

# --- 1. PUBLER API (The Hidden Gem) ---
# Ye method tumhara IP use nahi karega, ye Publer ke servers use karega.
def try_publer_api(url):
    api_url = "https://app.publer.io/hooks/media"
    
    payload = {
        "url": url,
        "iphone": False
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://publer.io/"
    }

    try:
        print("🚀 Trying Publer API...")
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Publer kabhi 'job_id' deta hai (processing) ya direct 'payload'
            
            if 'payload' in data and len(data['payload']) > 0:
                # Direct link mil gaya
                return data['payload'][0]['path']
            elif 'job_id' in data:
                # Agar video process ho rahi hai, to wait karna padta hai
                return check_publer_job(data['job_id'])
                
    except Exception as e:
        print(f"❌ Publer API Failed: {e}")
    
    return None

def check_publer_job(job_id):
    # Agar Publer bole "Wait karo", to hum status check karenge
    status_url = f"https://app.publer.io/api/v1/jobs/{job_id}"
    
    for _ in range(5): # 5 baar check karenge (total 10 seconds)
        time.sleep(2)
        try:
            res = requests.get(status_url)
            data = res.json()
            if 'payload' in data and len(data['payload']) > 0:
                return data['payload'][0]['path']
            if data.get('status') == 'failed':
                return None
        except:
            pass
    return None

# --- 2. INTERNAL ENGINE (Backup: yt-dlp) ---
def try_internal_ytdlp(url):
    print("⚠️ APIs failed. Switching to Internal Engine (yt-dlp)...")
    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'url' in info:
                return info['url']
            elif 'entries' in info:
                return info['entries'][0]['url']
                
    except Exception as e:
        print(f"❌ Internal Engine Failed: {e}")
        return None

# --- ROUTES ---
@app.route('/')
def home():
    return "VideosSonic (Publer + yt-dlp) Backend Running!"

@app.route('/download', methods=['POST'])
def get_video():
    data = request.json
    video_url = data.get('url')
    
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    print(f"\nProcessing: {video_url}")
    
    # Step 1: Publer API (External)
    direct_link = try_publer_api(video_url)
    
    # Step 2: yt-dlp (Internal Backup)
    if not direct_link:
        direct_link = try_internal_ytdlp(video_url)
    
    if direct_link:
        print("✅ Video Link Found!")
        return jsonify({"status": "success", "download_url": direct_link})
    else:
        return jsonify({"status": "error", "message": "Could not fetch video. Server might be blocked."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
