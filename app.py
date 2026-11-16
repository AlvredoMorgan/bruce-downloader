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

   # 2. Jalur YouTube via API Publik (Menghindari blokir IP Datacenter Vercel)
    if "youtube.com" in url or "youtu.be" in url:
        # Coba via Cobalt API (instance publik)
        cobalt_instances = [
            "https://api.cobalt.tools/",
            "https://cobalt-api.kwiatekmiki.com/"
        ]
        for api in cobalt_instances:
            try:
                payload = json.dumps({"url": url, "videoQuality": "720"}).encode("utf-8")
                req = urllib.request.Request(
                    api,
                    data=payload,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as res:
                    cdata = json.loads(res.read().decode("utf-8"))
                    if cdata.get("url"):
                        # Ambil juga versi audionya
                        audio_link = ""
                        try:
                            apayload = json.dumps({"url": url, "downloadMode": "audio"}).encode("utf-8")
                            areq = urllib.request.Request(api, data=apayload, headers={"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, method="POST")
                            with urllib.request.urlopen(areq, timeout=8) as ares:
                                adata = json.loads(ares.read().decode("utf-8"))
                                audio_link = adata.get("url", "")
                        except Exception:
                            pass

                        return {
                            "success": True,
                            "title": cdata.get("filename") or "Video YouTube",
                            "thumbnail": f"https://img.youtube.com/vi/{extract_yt_id(url)}/hqdefault.jpg" if extract_yt_id(url) else "",
                            "downloadUrl": cdata["url"],
                            "audioUrl": audio_link
                        }
            except Exception:
                continue

        return {"success": False, "error": "Server YouTube sedang membatasi akses. Gunakan link TikTok untuk hasil instan."}

    return {"success": False, "error": "Tautan tidak didukung. Masukkan tautan TikTok atau YouTube."}
