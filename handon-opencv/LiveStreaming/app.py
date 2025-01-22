import cv2
import yt_dlp
import numpy as np
import backend as bk
import time 


fps = 0
frame_counter = 0
start_time = time.time()

def openStream():
    global fps, frame_counter, start_time
    stream_url = bk.get_youtube_stream_url()
    if not stream_url:
        print("Failed to get stream URL.")
        return

    cap = cv2.VideoCapture(stream_url)
    
    if not cap.isOpened():
        print("Error: Unable to open video stream.")
        return

    frame_width, frame_height = 600, 300

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Stream ended or interrupted.")
            break
        frame_counter += 1
        elapsed_time = time.time() - start_time

        if elapsed_time > 1.0:  # Calculate FPS every second
            fps = round(frame_counter / elapsed_time)
            start_time = time.time()
            frame_counter = 0
        frame = cv2.resize(frame, (frame_width, frame_height), interpolation=cv2.INTER_AREA)
        cv2.putText(frame, f'FPS: {fps}', (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('YouTube Live Stream', frame)
        
        # Reduce CPU usage by adjusting wait time dynamically
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    openStream()
