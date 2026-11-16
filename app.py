from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import urllib.request
import urllib.parse
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Mesin Downloader Bruce di Vercel aktif!"}

@app.get("/download")
def get_video(url: str):
    if not url:
        return {"success": False, "error": "Link video kosong."}

    # 1. Jalur TikTok (Video No Watermark + Audio MP3)
    if "tiktok.com" in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
            req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as res:
                data = json.loads(res.read().decode("utf-8"))
                if data.get("code") == 0 and data.get("data", {}).get("play"):
                    tdata = data["data"]
                    music_info = tdata.get("music_info") or {}
                    audio_link = tdata.get("music") or music_info.get("play") or tdata["play"]
                    return {
                        "success": True,
                        "title": tdata.get("title") or "Video TikTok Tanpa Watermark",
                        "thumbnail": tdata.get("cover", ""),
                        "downloadUrl": tdata["play"],
                        "audioUrl": audio_link
                    }
        except Exception:
            pass
        return {"success": False, "error": "Gagal memproses video TikTok."}

    # 2. Jalur YouTube & Platform Lain dengan yt-dlp + Cookies
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }

    yt_cookies = os.environ.get("YT_COOKIES")
    if yt_cookies:
        cookie_path = "/tmp/cookies.txt"
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(yt_cookies)
        ydl_opts['cookiefile'] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            audio_url = ''

            if 'formats' in info:
                if not video_url:
                    for f in reversed(info['formats']):
                        if f.get('ext') == 'mp4' and f.get('url') and f.get('acodec') != 'none':
                            video_url = f.get('url')
                            break
                for f in reversed(info['formats']):
                    if f.get('vcodec') == 'none' and f.get('acodec') != 'none' and f.get('url'):
                        audio_url = f.get('url')
                        break

            if video_url:
                return {
                    "success": True,
                    "title": info.get('title', 'Video Siap Diunduh'),
                    "thumbnail": info.get('thumbnail', ''),
                    "downloadUrl": video_url,
                    "audioUrl": audio_url or video_url
                }
            return {"success": False, "error": "Gagal mengekstrak link video."}

    except Exception as e:
        return {"success": False, "error": f"YouTube Error: {str(e)}"}
