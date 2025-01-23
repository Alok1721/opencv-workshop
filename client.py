import socket
import json
import pygame
import colorsys
import cv2
import base64
import numpy as np
import threading

pygame.init()


HOST, PORT = "localhost", 6060
PLAYER_ID = "Alok"
BUFF_SIZE = 65536

WIDTH, HEIGHT = 1000, 600
SHAPES_LIST_WIDTH = 300
VIDEO_WIDTH = WIDTH - SHAPES_LIST_WIDTH
SHAPES_LIST_HEIGHT = HEIGHT
SHAPE_OFFSET_Y = 350

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
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    color_ranges = {
        'red': [
            (np.array([0, 100, 100]), np.array([10, 255, 255])),
            (np.array([160, 100, 100]), np.array([180, 255, 255]))
        ],
        'blue': [(np.array([90, 50, 50]), np.array([130, 255, 255]))],
        'green': [(np.array([30, 50, 50]), np.array([90, 255, 255]))]

    }
    result_list = []

    for color_name, ranges in color_ranges.items():
        color_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        color_mask = cv2.GaussianBlur(color_mask, (5, 5), 0)
        kernel = np.ones((5, 5), np.uint8)
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)
        for lower, upper in ranges:
            mask = cv2.inRange(hsv, lower, upper)
            color_mask = cv2.bitwise_or(color_mask, mask)

        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if cv2.contourArea(contour) < 50:
                continue

            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])
            


            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
            num_vertices = len(approx)

            if num_vertices == 3:
                shape = "triangle"
            elif num_vertices == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                shape = "square" if 0.90 <= aspect_ratio <= 1.1 else "rectangle"
            elif num_vertices > 4:
                shape = "circle"
            else:
                continue

            result_list.append({
                'shape': shape,
                'color': color_name,
                'center_x': center_x,
                'center_y': center_y,
            })
            cv2.putText(frame, str(shape), (center_x, center_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.drawContours(frame, [approx], 0, (255, 255, 255), -1)
            x, y, w, h = cv2.boundingRect(approx)

    return frame, result_list


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zine CV - Client")
font = pygame.font.Font(None, 28)

class Player:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.last_processed_frame = None
        self.running = False
        self.processed_frame = False
        self.frame_result = []
        self.name = PLAYER_ID
        self.score = 0
        self.tries = 0

    def send_data(self, data):
        try:
            json_data = json.dumps(data)
            self.socket.sendall(json_data.encode('utf-8'))
        except Exception as e:
            print(f"Error sending data: {e}")

    def receive_data(self):
        while self.running:
            try:
                data = self.socket.recv(BUFF_SIZE)
                if not data:
                    self.running = False
                    print("Connection closed by server")
                    break

                try:
                    json_data = json.loads(data.decode('utf-8'))
                    if json_data['type'] == 'video_frame':
                        self.process_frame(json_data['frame'])
                    elif json_data['type'] == 'result':
                        # print(f"Received results: {json_data}")
                        self.score = json_data['score']
                except json.JSONDecodeError:
                    print("Failed to decode JSON data")
            except Exception as e:
                print(f"Error receiving data: {e}")
                break
    
    def close_connection(self):
        self.socket.close()

    def process_frame(self, frame):
        nparr = np.frombuffer(base64.b64decode(frame), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is not None:
            if self.processed_frame:
                frame, self.frame_result = identify_shapes_and_colors(frame)
                self.last_processed_frame = frame.copy()

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame_surface = pygame.surfarray.make_surface(frame)
            screen.blit(frame_surface, (0, 0))

            if self.last_processed_frame is not None:
                processed_frame_rgb = cv2.cvtColor(self.last_processed_frame, cv2.COLOR_BGR2RGB)
                processed_frame_rgb = np.rot90(processed_frame_rgb)
                processed_frame_surface = pygame.surfarray.make_surface(processed_frame_rgb)

                processed_frame_x = VIDEO_WIDTH - processed_frame_surface.get_width() // 2
                screen.blit(processed_frame_surface, (processed_frame_x, 0))

            if self.processed_frame:
                pygame.draw.rect(screen, (0, 0, 0), (VIDEO_WIDTH + 10, SHAPE_OFFSET_Y, SHAPES_LIST_WIDTH, SHAPES_LIST_HEIGHT))
                print(self.frame_result)
                print(len(self.frame_result))
                for i, obj in enumerate(self.frame_result):
                    text = f"{obj['shape']} - {obj['color']}"
                    color = BASIC_COLORS.get(obj['color'], (255, 255, 255))
                    text_surface = font.render(text, True, color)
                    screen.blit(text_surface, (VIDEO_WIDTH + 10, SHAPE_OFFSET_Y + i * 30))
                self.processed_frame = False

    def send_shapes_to_server(self):
        self.send_data({"player_id": self.name, "shapes": self.frame_result})

    def run(self):
        self.socket.connect((HOST, PORT))
        self.send_data({"player_id": self.name})

        self.running = True
        socket_thread = threading.Thread(target=self.receive_data, daemon=True)
        socket_thread.start()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if 50 <= x <= 250 and HEIGHT - 100 <= y <= HEIGHT - 50:
                        self.processed_frame = True
                    elif 550 <= x <= 750 and HEIGHT - 100 <= y <= HEIGHT - 50:  # Send Shapes button
                        self.send_shapes_to_server()

            pygame.draw.rect(screen, (0, 255, 0), (50, HEIGHT - 100, 200, 50))
            pygame.draw.rect(screen, (255, 0, 0), (300, HEIGHT - 100, 200, 50))
            pygame.draw.rect(screen, (0, 0, 255), (550, HEIGHT - 100, 200, 50))  # Blue button

            process_text = font.render("Process Frame", True, (255, 255, 255))
            disconnect_text = font.render("Disconnect", True, (255, 255, 255))
            send_shapes_text = font.render("Send Shapes", True, (255, 255, 255))
            score_text = font.render(f"Score: {self.score}", True, (255, 255, 255))

            screen.blit(process_text, (50 + 100 - process_text.get_width() // 2, HEIGHT - 90))
            # screen.blit(disconnect_text, )
            screen.blit(send_shapes_text, (550 + 100 - send_shapes_text.get_width() // 2, HEIGHT - 90))
            screen.blit(score_text, (300 + 100 - disconnect_text.get_width() // 2, HEIGHT - 90))

            pygame.display.update()

        self.close_connection()
        socket_thread.join()

if __name__ == "__main__":
    player = Player()
    player.run()
    pygame.quit()
    print("[INFO] Disconnected")