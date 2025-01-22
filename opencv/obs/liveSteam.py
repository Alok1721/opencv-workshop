import cv2
import yt_dlp
import numpy as np

def get_youtube_stream_url():
    video_url = "https://www.youtube.com/watch?v=T0E6H4Ko8gs"
    ydl_opts = {
        'format': 'best',
        'quiet': True,  # Suppresses unnecessary logs
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        stream_url = info['url']
        return stream_url
