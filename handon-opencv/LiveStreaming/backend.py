import cv2
import yt_dlp
import numpy as np

def get_youtube_stream_url():
    video_url = "https://www.youtube.com/watch?v=T0E6H4Ko8gs"
    ydl_opts = {
        'format': 'best[height<=480]',

        'quiet': True,  # Suppresses unnecessary logs
        'noplaylist': True,  # Avoid processing entire playlists
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            return info['url']
        except Exception as e:
            print(f"Error fetching stream URL: {e}")
            return None