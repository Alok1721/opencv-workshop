import pygame
import threading
import cv2
import components
import base64
from server import SocketInterface


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
teams = []
scores = {}
correct_result = [[1, 2], [3, 5], [6, 7], [5, 6]]
players = []  # Store players as instances of Player class
accepting_clients = True

# Video Capture for webcam
cap = cv2.VideoCapture(0)  # Use webcam
ret, frame = False, None

def get_frame_answer(frame):
    shapes = []
    # do opencv stuff and 
    # shapes.append(['Circle', 'red', [255, 0, 0]])
    return shapes

class Player:
    def __init__(self, client_addr):
        self.client_addr = client_addr
        self.score = 0
        self.tries = 0
        self.stage = 0


class Manager:
    def __init__(self):
        self.socket_interface = SocketInterface(self)
        self.running = True

        self.ret, self.frame = False, None

    def process_player_data(self, player_id, data):
        # {'shapes': [['Circle', 'invalid', [255, 255, 255]], ['Triangle', 'invalid', [255, 255, 255]], ['Circle', 'invalid', [255, 255, 255]], ['Triangle', 'blue', [0, 0, 255]], ['Circle', 'red', [255, 0, 0]], ['Rectangle', 'green', [0, 255, 0]], ['Triangle', 'invalid', [255, 255, 255]], ['Circle', 'invalid', [255, 255, 255]]]}
        player_shapes = data.get("shapes", [])
        # evaluate player data

        validation_data = get_frame_answer(self.frame)
        correct = 0
        for i in range(len(validation_data)):
            if validation_data[i] in player_shapes[i]:
                correct += 1

        self.socket_interface.send_to_client(player_id, {
            "type": "result",
            "score": correct,
            "stage": 1
        })


    def draw_main_screen(self):
        """Draw the main screen (without video) for server interface."""
        screen.blit(bg, (0, 0))

        title = components.font.render("PARTICIPANTS", True, components.BLUE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        start_y = 150
        for idx, player in enumerate(players):
            pygame.draw.rect(screen, components.GRAY, (WIDTH // 2 - 150, start_y + idx * 60, 300, 50), border_radius=10)
            text = components.font.render(f"{player.client_addr} (Score: {player.score}, Tries: {player.tries}, Stage: {player.stage})", True, components.BLACK)
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
