import socket
import base64
import pygame
import threading
import numpy as np
import colorsys
import cv2
import json

# Constants
BUFF_SIZE = 65536
host_ip = 'localhost'  # Change this to your server's IP
port = 6060
WIDTH, HEIGHT = 1000, 600
SHAPES_LIST_WIDTH = 300
VIDEO_WIDTH = WIDTH - SHAPES_LIST_WIDTH
SHAPES_LIST_HEIGHT = HEIGHT
SHAPE_OFFSET_Y = 350

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zine CV - Client")
font = pygame.font.Font(None, 28)
last_processed_frame = None

# Client state
client_socket = None
shapes_list = []
stage1_response=[]
running = True
frame_processed = False

BASIC_COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "black": (0, 0, 0),
      "invalid": (255, 255, 255),
    "white": (255, 255, 255)
}

def get_simplified_color_name(hsv_color):
    """Map HSV color to red, green, blue, or invalid."""
    h, s, v = hsv_color

    if s < 0.2 or v < 0.2: #low saturation or value, invalid
        return "invalid"
    elif 0 <= h <= 20 or 160 <= h <= 180:  # Red (wraps around)
        return "red"
    elif 40 <= h <= 80:  # Green
        return "green"
    elif 100 <= h <= 140:  # Blue
        return "blue"
    else:
        return "invalid"
    
def hsv_to_rgb(hsv_color):
    """Convert HSV color to RGB."""
    h, s, v = hsv_color
    h = h/180.0
    s = s/255
    v = v/255
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))

def identify_shapes_and_colors(frame):
    """Identify shapes and colors using simplified HSV mapping."""
    global shapes_list
    shapes_list.clear()

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define range of white color in HSV
    lower_white = np.array([0,0,200])
    upper_white = np.array([180,30,255])

    # Threshold the HSV image to get only white colors
    mask = cv2.inRange(hsv, lower_white, upper_white)

    # Bitwise-AND mask and original image
    res = cv2.bitwise_and(frame,frame, mask= mask)

    gray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    frame_area = frame.shape[0] * frame.shape[1]

    for contour in contours:
        epsilon = 0.04 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        contour_area = cv2.contourArea(contour)
        min_area_threshold = frame_area * 0.001
        if contour_area < min_area_threshold:
            continue

        if len(approx) == 3:
            shape = "Triangle"
        elif len(approx) == 4:
            shape = "Rectangle"
        elif len(approx) > 4:
            shape = "Circle"
        else:
            continue

        mask = np.zeros_like(frame, dtype=np.uint8)
        cv2.drawContours(mask, [approx], 0, (255, 255, 255), -1)
        mask_gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        mask_gray[mask_gray > 0] = 255

        mean_hsv = cv2.mean(hsv, mask=mask_gray)[:3]
        color_name = get_simplified_color_name(mean_hsv)
        color_rgb = BASIC_COLORS[color_name]  # Get RGB from HSV

        x, y, w, h = cv2.boundingRect(approx)
        shapes_list.append((shape, color_name, color_rgb))  # Store RGB

        cv2.drawContours(frame, [approx], -1, color_rgb, 3)  # Use RGB for drawing

    return frame

def receive_message():
    global client_socket, frame_processed, last_processed_frame
    while running:
        try:
            msg = client_socket.recv(BUFF_SIZE)
            if msg:
                try:
                    json_data = json.loads(msg.decode('utf-8'))
                    if json_data['type'] == 'video_frame':
                        receive_video(json_data['frame'])
                    elif json_data['type'] == 'results':
                        print(f"[INFO] Received results: {json_data['results']}")
                except json.JSONDecodeError:
                    print(f"[ERROR] Failed to decode JSON data")
            else:
                print("[INFO] Connection closed by server")
                break
         
        except socket.error as e:
            print(f"[ERROR] Error receiving data from {e}")
        except Exception as e:
            print(f"[ERROR] Error: {e}")
            break


def receive_video(message):
    """Receive and display video stream."""
    global frame_processed, last_processed_frame
    frame_data = base64.b64decode(message)
    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is not None:
        if frame_processed:
            frame = identify_shapes_and_colors(frame)
            last_processed_frame = frame.copy()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.rot90(frame)
        frame_surface = pygame.surfarray.make_surface(frame)
        screen.blit(frame_surface, (0, 0))

        if last_processed_frame is not None:
            processed_frame_rgb = cv2.cvtColor(last_processed_frame, cv2.COLOR_BGR2RGB)
            processed_frame_rgb = np.rot90(processed_frame_rgb)
            processed_frame_surface = pygame.surfarray.make_surface(processed_frame_rgb)

            processed_frame_x = VIDEO_WIDTH - processed_frame_surface.get_width() // 2
            screen.blit(processed_frame_surface, (processed_frame_x, 0))

        if frame_processed:
            draw_shape_list()
            frame_processed = False

        # pygame.display.update()

  

def draw_shape_list():
    """Draw the list of identified shapes."""
    pygame.draw.rect(screen, (0, 0, 0), (VIDEO_WIDTH // 2 + VIDEO_WIDTH//4, 0, SHAPES_LIST_WIDTH, SHAPES_LIST_HEIGHT))
    y_offset = SHAPE_OFFSET_Y
    for shape, color_name, color in shapes_list:
        shape_text = font.render(f"{shape} - {color_name}", True, color)
        text_x = (VIDEO_WIDTH//2 + VIDEO_WIDTH//4) + (SHAPES_LIST_WIDTH // 2 - shape_text.get_width() // 2)
        screen.blit(shape_text, (text_x, y_offset))
        y_offset += 30

def send_shapes_to_server():
    """Send the current shapes list to the server."""
    global shapes_list, client_socket
    try:
        shapes_data = json.dumps({"shapes": shapes_list})  # Convert shapes list to JSON format
        client_socket.send(shapes_data.encode('utf-8'))
        print("[INFO] Shapes list sent to server.")
    except Exception as e:
        print(f"[ERROR] Error sending shapes list: {e}")

def start_client():
    """Connect to the server and handle events."""
    global client_socket, running
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_thread = threading.Thread(target=receive_message, daemon=True)

    try:
        client_socket.connect((host_ip, port))
        if not client_socket:
            print("[ERROR] Failed to connect to server")
            return
        
        # client_socket.sendto("REQUEST_STREAM".encode('utf-8'), (host_ip, port))
        print("[INFO] Connected to server")
        sock_thread.start()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if 50 <= x <= 250 and HEIGHT - 100 <= y <= HEIGHT - 50:
                        process_frame()
                    elif 300 <= x <= 500 and HEIGHT - 100 <= y <= HEIGHT - 50:
                        running = False
                    elif 550 <= x <= 750 and HEIGHT - 100 <= y <= HEIGHT - 50:  # Send Shapes button
                        send_shapes_to_server()

            # Draw buttons
            pygame.draw.rect(screen, (0, 255, 0), (50, HEIGHT - 100, 200, 50))
            pygame.draw.rect(screen, (255, 0, 0), (300, HEIGHT - 100, 200, 50))
            pygame.draw.rect(screen, (0, 0, 255), (550, HEIGHT - 100, 200, 50))  # Blue button

            process_text = font.render("Process Frame", True, (255, 255, 255))
            disconnect_text = font.render("Disconnect", True, (255, 255, 255))
            send_shapes_text = font.render("Send Shapes", True, (255, 255, 255))

            screen.blit(process_text, (50 + 100 - process_text.get_width() // 2, HEIGHT - 90))
            screen.blit(disconnect_text, (300 + 100 - disconnect_text.get_width() // 2, HEIGHT - 90))
            screen.blit(send_shapes_text, (550 + 100 - send_shapes_text.get_width() // 2, HEIGHT - 90))

            pygame.display.update()

    except Exception as e:
        print(f"[ERROR] Error: {e}")
    finally:
        if sock_thread.is_alive():
            sock_thread.join()

        if client_socket:
            client_socket.close()
        pygame.quit()
        print("[INFO] Disconnected")

def process_frame():
    """Set the flag to process the frame."""
    global frame_processed
    frame_processed = True
    print("[INFO] Processing frame...")

if __name__ == "__main__":
    start_client()
