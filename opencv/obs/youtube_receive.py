from datetime import timedelta
from dataclasses import dataclass
import yt_dlp
import numpy as np
import cv2

valid_resolutions = ['144p', '240p', '360p', '480p', '720p', '720p60', '1080p', '1080p60']

@dataclass
class VideoStream:
    url: str = None
    resolution: str = None
    height: int = 0
    width: int = 0

    def __init__(self, video_format: dict):
        self.url = video_format['url']
        self.resolution = video_format['format_note']
        self.height = video_format['height']
        self.width = video_format['width']

    def __str__(self):
        return f'{self.resolution} ({self.height}x{self.width}): {self.url}'

ydl_opts = {
    'cookiefile': 'cookies.txt',  # Path to the exported cookies file
    'format': 'best'
}


def list_video_streams(url: str) -> tuple[list[VideoStream], np.ndarray]:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # Print available formats for debugging
        for f in info['formats']:
            print(f"Format: {f['format_id']} - {f.get('format_note')} - {f.get('url')}")

        filter = lambda x: x['vcodec'] != 'none' and 'format_note' in x and x['format_note'] in valid_resolutions
        streams = [VideoStream(format) for format in info['formats'][::-1] if filter(format)]

        if not streams:
            print("No valid streams found!")
            return [], np.array([])

        _, unique_indices = np.unique(np.array([stream.resolution for stream in streams]), return_index=True)
        streams = [streams[index] for index in np.sort(unique_indices)]
        resolutions = np.array([stream.resolution for stream in streams])
        return streams[::-1], resolutions[::-1]

# def list_video_streams(url: str) -> tuple[list[VideoStream], np.ndarray]:
#     # ℹ️ See help(yt_dlp.YoutubeDL) for a list of available options and public functions
#     ydl_opts = {}
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(url, download=False)

#         filter = lambda x: x['vcodec'] != 'none' and 'format_note' in x and x['format_note'] in valid_resolutions
#         streams = [VideoStream(format) for format in info['formats'][::-1] if filter(format)]
#         _, unique_indices = np.unique(np.array([stream.resolution
#                                                 for stream in streams]), return_index=True)
#         streams = [streams[index] for index in np.sort(unique_indices)]
#         resolutions = np.array([stream.resolution for stream in streams])
#         return streams[::-1], resolutions[::-1]


def cap_from_youtube(url: str,
                     resolution: str = 'best',
                     start: timedelta = timedelta(seconds=0)) -> cv2.VideoCapture:

    streams, resolutions = list_video_streams(url)

    if resolution == 'best':
        resolution = resolutions[-1]

    if resolution not in resolutions:
        raise ValueError(f'Resolution {resolution} not available')

    res_index = np.where(resolutions == resolution)[0][0]
    cap = cv2.VideoCapture(streams[res_index].url)
    fps = cap.get(cv2.CAP_PROP_FPS)

    start_frame = int(start.total_seconds() * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    return cap


if __name__ == '__main__':
    youtube_url = 'https://www.youtube.com/watch?v=8blucOU11Bo'

    # Get the best resolution available
    cap = cap_from_youtube(youtube_url, resolution='best')

    if not cap.isOpened():
        print("Error: Could not open video stream.")
        exit()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("End of video or stream error.")
            break

        cv2.imshow('YouTube Video', frame)

        # Exit when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()