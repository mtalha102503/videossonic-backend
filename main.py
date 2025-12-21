from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

def cobalt_download(url):
    # Bilkul naye aur active servers ki list (Updated Dec 2025)
    servers = [
        "https://cobalt.lacwx.net/api/json",      # Reliable Server 1
        "https://api.cobalt.mashed.pw/api/json",  # Reliable Server 2
        "https://cobalt.q1.dj/api/json",          # Backup Server 3
        "https://cobalt.stream/api/json"          # Backup Server 4
    ]
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    payload = {
        "url": url,
        # 'vQuality' hata dia kyunki naye servers 'filenamePattern' prefer krte hain
        "filenamePattern": "basic"
    }

    # Loop chalayenge: Bari bari sabko try karenge
    for api_url in servers:
        try:
            print(f"Trying server: {api_url}") 
            response = requests.post(api_url, headers=headers, json=payload, timeout=15)
            data = response.json()
            
            # Debugging ke liye print
            # print(f"Response from {api_url}: {data}")

            # Check karo agar URL mila ya status 'stream'/'redirect' hai
            if 'url' in data:
                return data['url']
            elif 'status' in data and data['status'] == 'stream':
                return data['url']
            elif 'status' in data and data['status'] == 'redirect':
                return data['url']
            
            # Agar server ne mana kia
            print(f"Failed on {api_url}: {data}")
            
        except Exception as e:
            print(f"Error connecting to {api_url}: {e}")
            continue # Agle server par jao

    return None # Agar sab fail ho gaye

@app.route('/')
def home():
    return "VideosSonic Backend is Running!"

@app.route('/download', methods=['POST'])
def get_video():
    data = request.json
    video_url = data.get('url')
    
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    print(f"Processing URL: {video_url}") 
    direct_link = cobalt_download(video_url)
    
    if direct_link:
        return jsonify({"status": "success", "download_url": direct_link})
    else:
        return jsonify({"status": "error", "message": "Servers busy. Please try again."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
