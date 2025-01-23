import pygame
import threading
import cv2
import components
import base64
from server import SocketInterface
import numpy as np


# Constants
BUFF_SIZE = 65536
host_ip = 'localhost'  # Change this to your server's IP
port = 6060

# Set up display for Pygame (for interface)
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zine CV - Server")

# Load background image
bg = pygame.image.load("back.jpg")
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))

# Server state
correct_result = [[1, 2], [3, 5], [6, 7], [5, 6]]

# Video Capture for webcam
cap = cv2.VideoCapture(0)  # Use webcam
ret, frame = False, None

def get_frame_answer(frame):
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

class Player:
    def __init__(self, player_id):
        self.player_id = player_id
        self.sent_response = False
        self.score = 0
        self.stage = 0
        self.tries = 0


class Manager:
    def __init__(self):
        self.socket_interface = SocketInterface(self)
        self.running = True
        self.players: dict[str, Player] = {'AlokAlokAlok': Player('AlokAlokAlok')}
        self.accepting_responses = True
        self.accepting_players = False

        self.mode = "main_screen"
        self.ret, self.frame = False, None

    def process_player_data(self, player_id, data):
        # [{'shape': 'circle', 'color': 'red', 'center_x': 237, 'center_y': 222}, {'shape': 'circle', 'color': 'red', 'center_x': 246, 'center_y': 251}]
        if not player_id:
            return

        player_shapes = data.get("shapes", [])
        player = self.players.get(player_id)
        if not player:
            self.players[player_id] = Player(player_id)
            player = self.players[player_id]

        if not player_shapes or not self.accepting_responses or player.sent_response:
            return
        
        frame, validation_data = get_frame_answer(self.frame)
        shape_list = [(s['shape'], s['color']) for s in validation_data]
        response_list = [(s['shape'], s['color']) for s in player_shapes]
        correct = 0
        for i in range(len(shape_list)):
            if shape_list[i] in response_list:
                correct += 1

        player.sent_response = True
        player.score += correct
        player.tries += 1
        print(f"Player {player_id} got {correct} out of {len(validation_data)} correct.")
        self.socket_interface.send_to_client(player_id, {
            "type": "result",
            "score": player.score,
            "stage": 1
        })

    def draw_main_screen(self):
        """Draw the main screen (without video) for server interface."""
        screen.blit(bg, (0, 0))

        title = components.font.render("PARTICIPANTS", True, components.BLUE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))
        
        start_x, start_y = 135, 80
        column_width = 240
        padding_x, padding_y = 25, 40

        sorted_players = sorted(self.players.values(), key=lambda x: x.score, reverse=True)
        for idx, player in enumerate(sorted_players):
            column = idx % 3
            row = idx // 3
            x = start_x - column_width // 2 + column * (column_width + padding_x)
            y = start_y + row * padding_y

            pygame.draw.rect(screen, components.GRAY, (x, y, column_width, 30), border_radius=10)
            text = components.small_font.render(f"{idx + 1}. {player.player_id[:20]}: {player.score} ({player.tries} tries)", True, components.BLACK)
            screen.blit(text, (x + (column_width - text.get_width()) // 2, y + 10))

        # Start Game Button
        pygame.draw.rect(screen, components.BLACK, (WIDTH // 2 - 102, HEIGHT - 82, 204, 54), border_radius=15)
        pygame.draw.rect(screen, components.BLUE, (WIDTH // 2 - 100, HEIGHT - 80, 200, 50), border_radius=15)
        btn_text = components.font.render("Stop" if self.accepting_players else "Start", True, components.WHITE)
        screen.blit(btn_text, (WIDTH // 2 - btn_text.get_width() // 2, HEIGHT - 70))

        # Accepting Clients Toggle Button
        toggle_color = components.GREEN if self.accepting_responses else components.RED
        pygame.draw.rect(screen, toggle_color, (50, HEIGHT - 80, 200, 50), border_radius=15)
        toggle_text = components.font.render("Server: " + ("ON" if self.accepting_responses else "OFF"), True, components.WHITE)
        screen.blit(toggle_text, (50 + 100 - toggle_text.get_width() // 2, HEIGHT - 70))

        pygame.display.flip()

    def run(self):
        cap = cv2.VideoCapture(0)
        socket_thread = threading.Thread(target=self.socket_interface.run_server)
        socket_thread.start()

        while self.running:
            try:
                self.ret, self.frame = cap.read()
                self.draw_main_screen()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = event.pos
                        # Check toggle button
                        if 50 <= x <= 250 and HEIGHT - 80 <= y <= HEIGHT - 30:
                            self.accepting_responses = not self.accepting_responses
                            for player in self.players.values():
                                player.sent_response = False

                        # Check start game button
                        elif WIDTH // 2 - 102 <= x <= WIDTH // 2 + 102 and HEIGHT - 82 <= y <= HEIGHT - 28:
                            self.accepting_players = not self.accepting_players
                            # self.socket_interface.accepting_connections = self.accepting_players

                # Broadcast the frame to all clients
                if self.ret:
                    cv2.imshow("CAMERA", self.frame)
                    frame = cv2.resize(self.frame, (400, 300))
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    message = base64.b64encode(buffer)

                    self.socket_interface.broadcast_to_clients({
                        "type": "video_frame",
                        "frame": message.decode('utf-8')
                    })
                
            except KeyboardInterrupt:
                self.running = False
                break
        
        socket_thread.join()


if __name__ == '__main__':
    manager = Manager()
    manager.run()
