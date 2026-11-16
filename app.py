from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import urllib.request
import urllib.parse
import json
import re

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

def extract_yt_id(url: str):
    match = re.search(r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else None

@app.get("/download")
def get_video(url: str):
    if not url:
        return {"success": False, "error": "Link video kosong."}

    # 1. Jalur TikTok (No Watermark)
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

    # 2. Jalur yt-dlp menyamar sebagai klien Android/iOS (Anti Bot-Check YouTube)
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'skip': ['webpage']
            }
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
    except Exception as e:
        yt_error = str(e)

    # 3. Jalur Cadangan YouTube via Piped API (Jika IP Vercel tetap diblokir YouTube)
    yt_id = extract_yt_id(url)
    if yt_id:
        piped_instances = [
            "https://pipedapi.kavin.rocks",
            "https://api.piped.private.coffee",
            "https://pipedapi.adminforge.de"
        ]
        for instance in piped_instances:
            try:
                req = urllib.request.Request(
                    f"{instance}/streams/{yt_id}",
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=8) as res:
                    pdata = json.loads(res.read().decode("utf-8"))
                    streams = pdata.get("videoStreams", [])
                    # Cari video MP4 yang sudah ada audionya (videoOnly == False)
                    for s in streams:
                        if s.get("format") == "MPEG_4" and not s.get("videoOnly") and s.get("url"):
                            return {
                                "success": True,
                                "title": pdata.get("title", "Video YouTube"),
                                "thumbnail": pdata.get("thumbnailUrl", ""),
                                "downloadUrl": s["url"]
                            }
            except Exception:
                continue

    return {"success": False, "error": "YouTube membatasi akses dari server saat ini. Coba link TikTok atau coba beberapa saat lagi."}
