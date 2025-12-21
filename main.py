from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

def cobalt_download(url):
    # Hum 3 alag alag servers try karenge bari bari
    servers = [
        "https://api.cobalt.tools/api/json",      # Official Server 1
        "https://cobalt7.moyin.site/api/json",    # Backup Server 2
        "https://cobalt.api.kwiatekmiki.pl/api/json" # Backup Server 3
    ]
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        # User-Agent lagana zaroori hai taki server ko lage browser hai
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    payload = {
        "url": url,
        "vQuality": "max"
    }

    # Loop chalayenge: Pehle server 1, fail hua to server 2...
    for api_url in servers:
        try:
            print(f"Trying server: {api_url}") # Logs me dikhega
            response = requests.post(api_url, headers=headers, json=payload, timeout=10)
            data = response.json()
            
            # Agar URL mil gaya to wapis bhej do
            if data.get('url'):
                return data.get('url')
            
            # Agar server ne mana kia, agla try kro
            print(f"Failed on {api_url}: {data}")
            
        except Exception as e:
            print(f"Error connecting to {api_url}: {e}")
            continue # Agle server par jao

    return None # Agar teeno fail ho gaye

@app.route('/')
def home():
    return "VideosSonic Backend is Running!"

@app.route('/download', methods=['POST'])
def get_video():
    data = request.json
    video_url = data.get('url')
    
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    print(f"Processing URL: {video_url}") # Log me URL print kro
    direct_link = cobalt_download(video_url)
    
    if direct_link:
        return jsonify({"status": "success", "download_url": direct_link})
    else:
        return jsonify({"status": "error", "message": "All servers failed. Try again later."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
