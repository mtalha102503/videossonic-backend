from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
# CORS enable kar rahe hain taki Hostinger se request block na ho
CORS(app)

def cobalt_download(url):
    # Backup instance try kar rahe hain
    api_url = "https://cobalt.api.kwiatekmiki.pl/api/json"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": url,
        "vQuality": "max"
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        data = response.json()
        return data.get('url')
    except Exception as e:
        print(f"Error: {e}")
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

    direct_link = cobalt_download(video_url)
    
    if direct_link:
        return jsonify({"status": "success", "download_url": direct_link})
    else:
        return jsonify({"status": "error", "message": "Could not fetch video"}), 500

if __name__ == '__main__':
    # Render dynamic port use karta hai
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
