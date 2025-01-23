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
teams = ["Team1", "Team2", "Team3", "Team4"]    
scores = {}
correct_result = [[1, 2], [3, 5], [6, 7], [5, 6]]
players = {} # Store players as instances of Player class
accepting_clients = True

# Video Capture for webcam
# cap = cv2.VideoCapture(1)  # Use webcam
# ret, frame = False, None

def get_frame_answer(frame):
    shapes = []
    # do opencv stuff and 
    # shapes.append(['Circle', 'red', [255, 0, 0]])
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
            shapes.append([shape, color_name])
    return shapes

class Player:
    def __init__(self, client_name):
        self.client_name = client_name
        self.score = 0
        self.tries = 10
        self.stage = 1


class Manager:
    def __init__(self):
        self.socket_interface = SocketInterface(self)
        self.running = True

        self.ret, self.frame = False, None

    def process_player_data(self, team_name, data):
        # {'shapes': [['Circle', 'invalid', [255, 255, 255]], ['Triangle', 'invalid', [255, 255, 255]], ['Circle', 'invalid', [255, 255, 255]], ['Triangle', 'blue', [0, 0, 255]], ['Circle', 'red', [255, 0, 0]], ['Rectangle', 'green', [0, 255, 0]], ['Triangle', 'invalid', [255, 255, 255]], ['Circle', 'invalid', [255, 255, 255]]]}
       
        print(f"Player {team_name} sent data: {data}")
        player_shapes = data.get("shapes", [])
        print(f"Player {team_name} sent {len(player_shapes)} shapes.")
        print(player_shapes)
        # evaluate player data

        validation_data = get_frame_answer(self.frame)
        correct = 0
        print(validation_data)
        for i in range(len(validation_data)):
            if validation_data[i] in player_shapes:
                correct += 10

        player = players[team_name]
        if len(player_shapes) > len(validation_data):
            correct-= (len(player_shapes) - len(validation_data))*5
            
        player.score = max(correct,player.score)
        player.stage = 1  
        player.tries -= 1
        self.socket_interface.send_to_client(team_name, {
            "type": "result",
            "score": player.score,
            "stage": player.stage
        })
    def create_player(self, team_name):
        if team_name not in teams:
            return
        players[team_name] = Player(team_name)

        
    def valid_player(self, team_name):
        if team_name not in teams:
            return False
        return True
    def remove_player(self, team_name):
        players.pop(team_name, None)
        

    def draw_main_screen(self):
        """Draw the main screen (without video) for server interface."""
        screen.blit(bg, (0, 0))

        title = components.font.render("PARTICIPANTS", True, components.BLUE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        start_y = 150
        for idx, player in enumerate(players.values()):
            pygame.draw.rect(screen, components.GRAY, (WIDTH // 2 - 300, start_y + idx * 60, 600, 50), border_radius=10)
            text = components.font.render(f"{player.client_name} (Score: {player.score}, Tries: {player.tries}, Stage: {player.stage})", True, components.BLACK)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, start_y + idx * 60 + 10))

        # Start Game Button
        pygame.draw.rect(screen, components.BLACK, (WIDTH // 2 - 102, HEIGHT - 152, 204, 54), border_radius=15)
        pygame.draw.rect(screen, components.BLUE, (WIDTH // 2 - 100, HEIGHT - 150, 200, 50), border_radius=15)
        btn_text = components.font.render("Start Game", True, components.WHITE)
        screen.blit(btn_text, (WIDTH // 2 - btn_text.get_width() // 2, HEIGHT - 140))

        # Accepting Clients Toggle Button
        toggle_color = components.GREEN if accepting_clients else components.RED
        pygame.draw.rect(screen, toggle_color, (50, HEIGHT - 150, 200, 50), border_radius=15)
        toggle_text = components.font.render("Server: " + ("ON" if accepting_clients else "OFF"), True, components.WHITE)
        screen.blit(toggle_text, (50 + 100 - toggle_text.get_width() // 2, HEIGHT - 140))

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
                        if 50 <= x <= 250 and HEIGHT - 150 <= y <= HEIGHT - 100:
                            accepting_clients = not accepting_clients

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
