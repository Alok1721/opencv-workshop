import cv2
import socket
import numpy as np
import base64
import time 

BUFF_SIZE = 65536
server_ip = 'localhost'  # Use your server's IP address
server_port = 8899

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)

message = b'Hello Server'
client_socket.sendto(message, (server_ip, server_port))

cv2.namedWindow('RECEIVING VIDEO', cv2.WINDOW_NORMAL)
fps = 0
frame_counter = 0
start_time = time.time()

while True:
    try:
        packet, _ = client_socket.recvfrom(BUFF_SIZE)
        data = base64.b64decode(packet)
        npdata = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(npdata, cv2.IMREAD_COLOR)

        frame_counter += 1
        elapsed_time = time.time() - start_time

        if elapsed_time > 1.0:  # Calculate FPS every second
            fps = round(frame_counter / elapsed_time)
            start_time = time.time()
            frame_counter = 0

        # Overlay FPS on the frame
        cv2.putText(frame, f'FPS: {fps}', (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("RECEIVING VIDEO", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    except Exception as e:
        print(f"Error: {e}")
        break

client_socket.close()
cv2.destroyAllWindows()
