import cv2
import liveSteam as ls 
def openStream():
    # ls.run_backend()
    stream_url= ls.get_youtube_stream_url()
    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        print("Error: Unable to open video stream.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream ended or interrupted.")
            break
        frame=cv2.resize(frame,(300,300))
        cv2.imshow('YouTube Live Stream', frame)

        # Press 'q' to exit the video window
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    openStream()