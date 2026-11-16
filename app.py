from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Mesin yt-dlp Bruce di Vercel aktif!"}

@app.get("/download")
def get_video(url: str):
    if not url:
        return {"success": False, "error": "Link video kosong."}

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
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
        return {"success": False, "error": f"Error yt-dlp: {str(e)}"}
