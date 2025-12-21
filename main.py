from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import yt_dlp  # Apna Engine Import kia

app = Flask(__name__)
CORS(app)

# --- 1. EXTERNAL API METHOD (Pehle ye try karega) ---
def try_cobalt_api(url):
    # Sirf 1-2 reliable servers rakhe hain
    servers = [
        "https://api.cobalt.tools/api/json",  # Official (Sometimes busy)
        "https://api.wuk.sh/api/json"         # Popular Alternative
    ]
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    payload = {
        "url": url,
        "filenamePattern": "basic"
    }

    for api_url in servers:
        try:
            print(f"Trying External API: {api_url}")
            response = requests.post(api_url, headers=headers, json=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'url' in data:
                    return data['url']
        except Exception as e:
            print(f"API Failed ({api_url}): {e}")
            continue
            
    return None

# --- 2. INTERNAL ENGINE METHOD (Backup: Khud Link Nikalo) ---
def try_internal_ytdlp(url):
    print("APIs failed. Starting Internal Engine (yt-dlp)...")
    try:
        ydl_opts = {
            'format': 'best',       # Best quality
            'quiet': True,          # Logs kam karo
            'no_warnings': True,
            'extract_flat': False,  # Pura info nikalo
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Link dhoondo
            if 'url' in info:
                return info['url']
            elif 'entries' in info:
                # Kabhi kabhi playlist hoti hai
                return info['entries'][0]['url']
                
    except Exception as e:
        print(f"Internal Engine Failed: {e}")
        return None

# --- ROUTES ---
@app.route('/')
def home():
    return "VideosSonic Hybrid Backend is Running!"

@app.route('/download', methods=['POST'])
def get_video():
    data = request.json
    video_url = data.get('url')
    
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    print(f"Processing: {video_url}")
    
    # 1. Pehle API Try karo (Fast)
    direct_link = try_cobalt_api(video_url)
    
    # 2. Agar API fail ho, to apna engine chalao (Reliable)
    if not direct_link:
        direct_link = try_internal_ytdlp(video_url)
    
    if direct_link:
        return jsonify({"status": "success", "download_url": direct_link})
    else:
        return jsonify({"status": "error", "message": "Could not fetch video. Server might be blocked."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
