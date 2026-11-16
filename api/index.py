from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import urllib.request
import urllib.parse
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/api")
@app.get("/api/index")
def home():
    return {"status": "Mesin Downloader Bruce aktif!"}

@app.get("/download")
@app.get("/api/download")
def get_video(url: str):
    if not url:
        return {"success": False, "error": "Link video kosong."}

    # Jalur TikTok (No Watermark)
    if "tiktok.com" in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
            req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as res:
                data = json.loads(res.read().decode("utf-8"))
                if data.get("code") == 0 and data.get("data", {}).get("play"):
                    return {
                        "success": True,
                        "title": data["data"].get("title") or "Video TikTok Tanpa Watermark",
                        "thumbnail": data["data"].get("cover", ""),
                        "downloadUrl": data["data"]["play"]
                    }
        except Exception:
            pass

    # Jalur yt-dlp (YouTube & platform lain)
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')

            if not video_url and 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('ext') == 'mp4' and f.get('url') and f.get('acodec') != 'none':
                        video_url = f.get('url')
                        break

            if video_url:
                return {
                    "success": True,
                    "title": info.get('title', 'Video Siap Diunduh'),
                    "thumbnail": info.get('thumbnail', ''),
                    "downloadUrl": video_url
                }
            return {"success": False, "error": "Gagal mengekstrak link MP4 langsung."}

    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}
