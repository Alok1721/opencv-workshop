import cv2
import imutils
import socket
import numpy as np
import base64
import threading

BUFF_SIZE = 65536
host_ip = '192.168.0.199'  # Change this to your server's IP address
port = 9999

MAX_CLIENTS = 10  # Limit the number of clients to 10
active_clients = []
lock = threading.Lock()

def handle_client(client_addr):
    """Function to send video frames to a connected client."""
    print(f"[INFO] Started thread for client: {client_addr}")

    # Create a new UDP socket inside the thread to handle the client
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    vid = cv2.VideoCapture(0)  # Use '0' for webcam, or replace with 'video.mp4'
    WIDTH = 400

    try:
        while vid.isOpened():
            ret, frame = vid.read()
            if not ret:
                print(f"[ERROR] Could not capture video for {client_addr}")
                break

            frame = imutils.resize(frame, width=WIDTH)
            encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            message = base64.b64encode(buffer)

            client_socket.sendto(message, client_addr)

            with lock:
                total_clients = len(active_clients)

            # Display number of active clients on the server screen
            frame = cv2.putText(frame, f'Total Clients: {total_clients}', (10, 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow(f"Client {client_addr}", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    except Exception as e:
        print(f"[ERROR] Error handling client {client_addr}: {e}")
    finally:
        vid.release()
        cv2.destroyAllWindows()
        client_socket.close()
        with lock:
            active_clients.remove(client_addr)
        print(f"[INFO] Closed connection with {client_addr}")

if __name__ == "__main__":
    # Create UDP socket for listening
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    socket_address = (host_ip, port)
    server_socket.bind(socket_address)

    print(f"[INFO] Server listening on {socket_address}")

    try:
        while True:
            # Receive initial client request
            msg, client_addr = server_socket.recvfrom(BUFF_SIZE)
            print(f"[INFO] New client request from: {client_addr}")

            with lock:
                if len(active_clients) < MAX_CLIENTS:
                    if client_addr not in active_clients:
                        user_response = input(f"Accept connection from {client_addr}? (y/n): ").strip().lower()
                        if user_response == 'y':
                            print(f"[INFO] Accepted connection from {client_addr}")
                            active_clients.append(client_addr)

                            # Start a new thread for each client
                            client_thread = threading.Thread(target=handle_client, args=(client_addr,))
                            client_thread.daemon = True  # Allows thread to close on main exit
                            client_thread.start()
                        else:
                            print(f"[INFO] Rejected connection from {client_addr}")
                    else:
                        print(f"[INFO] Client {client_addr} is already connected.")
                else:
                    print(f"[WARNING] Max client limit ({MAX_CLIENTS}) reached. Rejecting {client_addr}")

    except KeyboardInterrupt:
        print("\n[INFO] Shutting down server...")
        server_socket.close()
