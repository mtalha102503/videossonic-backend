from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

def cobalt_download(url):
    # Updated List of Working Cobalt Instances (Dec 2025)
    # Hum 'Shotgun Method' use kar rahe hain - jo chal gaya wo best!
    servers = [
        "https://cobalt.jas.bio/api/json",         # Server 1
        "https://cobalt.zip/api/json",             # Server 2
        "https://wuk.sh/api/json",                 # Server 3 (Classic)
        "https://cobalt.kwiatekmiki.pl/api/json",  # Server 4 (Fixed URL)
        "https://api.cobalt.kwiatekmiki.pl/api/json", # Server 5 (Alt URL)
        "https://cobalt.154.53.53.53.nip.io/api/json", # Server 6 (IP Based - often reliable)
        "https://cobalt.nao.20041124.xyz/api/json" # Server 7
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

    # Loop through all servers
    for api_url in servers:
        try:
            print(f"Trying server: {api_url}") 
            # Timeout kam rakha hai taki jaldi agla server try kare
            response = requests.post(api_url, headers=headers, json=payload, timeout=8)
            
            # Agar server 200 OK de raha hai tabhi JSON decode karo
            if response.status_code == 200:
                data = response.json()
                
                # Success Logic
                if 'url' in data:
                    print(f"✅ Success on {api_url}")
                    return data['url']
                elif 'status' in data and data['status'] in ['stream', 'redirect']:
                    print(f"✅ Success (Stream) on {api_url}")
                    return data['url']
            else:
                print(f"❌ Server {api_url} returned status: {response.status_code}")

        except Exception as e:
            # Agar connection fail ho jaye to error print karo aur next server par jao
            print(f"⚠️ Error connecting to {api_url}: {e}")
            continue

    return None

@app.route('/')
def home():
    return "VideosSonic Backend is Running!"

@app.route('/download', methods=['POST'])
def get_video():
    data = request.json
    video_url = data.get('url')
    
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    print(f"Processing Request for: {video_url}")
    direct_link = cobalt_download(video_url)
    
    if direct_link:
        return jsonify({"status": "success", "download_url": direct_link})
    else:
        # Agar saare servers fail ho jayen
        return jsonify({"status": "error", "message": "All servers are busy. Please try again later."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
