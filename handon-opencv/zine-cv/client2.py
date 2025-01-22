import pygame
import socket
import json
import time

# Initialize Pygame
pygame.init()
display_info = pygame.display.Info()
WIDTH, HEIGHT = 800, 600
center_x, center_y = (WIDTH // 2) - 180, HEIGHT // 2
screen = pygame.display.set_mode((WIDTH, HEIGHT))  # , pygame.FULLSCREEN
pygame.display.set_caption("Zine CV")

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
HOVER_COLOR = (10, 50, 99)
DEFAULT_BORDER_COLOR = (255, 255, 255)
HOVER_BORDER_COLOR = (0, 255, 0)
mode_selected_color = HOVER_COLOR

bg = pygame.image.load("score.jpg")
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
screen.blit(bg, (0, 0))

# Font setup
font = pygame.font.SysFont(None, 40)

team_name = "."
input_box = pygame.Rect(center_x, center_y - 100, 400, 40)

# Server Info
SERVER_IP = "127.0.0.1"
SERVER_PORT = 12345
test_result = [[1, 2], [3, 5], [6, 7], [5, 6]]


def draw_text(text, font, color, surface, x, y):
    label = font.render(text, True, color)
    surface.blit(label, (x, y))


def draw_button_with_hover(button_rect, text, x, y, hover_color, default_color, font, screen):
    """ Hover effect for buttons."""
    mouse_x, mouse_y = pygame.mouse.get_pos()
    if button_rect.collidepoint(mouse_x, mouse_y):
        pygame.draw.rect(screen, hover_color, button_rect)
        draw_text(text, font, WHITE, screen, x, y)
    else:
        pygame.draw.rect(screen, default_color, button_rect)
        draw_text(text, font, hover_color, screen, x, y)


def display_menu():
    screen.blit(bg, (0, 0))
    mouse_x, mouse_y = pygame.mouse.get_pos()
    input_box_border_color = HOVER_BORDER_COLOR if input_box.collidepoint(mouse_x, mouse_y) else DEFAULT_BORDER_COLOR
    pygame.draw.rect(screen, input_box_border_color, input_box, 2)
    draw_text(team_name, font, WHITE, screen, input_box.x + 10, input_box.y + 10)
    draw_text("Enter Team Name", font, WHITE, screen, center_x, center_y - 150)
    draw_text("Select Mode", font, WHITE, screen, center_x, center_y - 20)
    button_test_mode = pygame.Rect(center_x + 10, center_y + 15, 200, 50)
    button_game_mode = pygame.Rect(center_x + 10, center_y + 70, 200, 50)
    draw_button_with_hover(button_test_mode, "Test Mode", center_x + 20, center_y + 25, HOVER_COLOR, WHITE, font, screen)
    draw_button_with_hover(button_game_mode, "Game Mode", center_x + 20, center_y + 80, HOVER_COLOR, WHITE, font, screen)
    
    submit_button_obj = submit_button()
    stage_buttons = draw_stage_buttons()
    pygame.display.update()
    return button_test_mode, button_game_mode,submit_button_obj,stage_buttons
def submit_button():
    submit_button = pygame.Rect(center_x +10, center_y + 150, 200, 50)
    draw_button_with_hover(submit_button, "Submit", center_x +30, center_y + 170, GREEN, WHITE, font, screen)
    return submit_button


def draw_stage_buttons(start_y=150,selected_stage=0):
    """ Draw the stage buttons based on the selected mode."""
    test_stages = [0]
    game_stages = [1,2,3,4,5,6]
    stage_buttons = []

    # for i, stage in enumerate(test_stages):
    #     stage_button= pygame.Rect(center_x + 10, start_y + i * 60, 200, 50)
    #     stage_buttons.append(stage_button)
    #     draw_button_with_hover(stage_button, f"Stage {stage}", center_x + 20, start_y + i * 60 + 10, HOVER_COLOR, WHITE, font, screen)
    pygame.Rect(center_x + 200, start_y  - 20, 50, 50)
    draw_text("Select Stage", font, WHITE, screen, center_x, start_y  + 20)
    for i, stage in enumerate(game_stages):
        
        stage_button=pygame.Rect(center_x + 400, start_y + i * 60, 50, 50)
        stage_buttons.append(stage_button)
        draw_button_with_hover(stage_button, f"{stage}", center_x + 20, start_y + i * 60 + 10, HOVER_COLOR, WHITE, font, screen)
        if i == selected_stage:
            pygame.draw.rect(screen, GREEN, stage_button)  # Highlight selected stage
        else:
            pygame.draw.rect(screen, WHITE, stage_button)  # Normal state
        
    # pygame.display.update()
    return stage_buttons


def start_client(mode, stage):
    global test_result
    global team_name
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_IP, SERVER_PORT))
    print(f"inside the start_client {team_name} - Mode: {mode}, Stage: {stage}")
    try:
        while True:
            if mode == 'game':
                data = {
                    "name": team_name,
                    "result": test_result,
                    "mode": mode,
                    "stage": stage
                }
                json_data = json.dumps(data)
                client.sendall(json_data.encode("utf-8"))
                print(f"Sent data: {json_data}")
            time.sleep(2)

    except KeyboardInterrupt:
        print("Client disconnected.")
    finally:
        client.close()


def main():
    global team_name
    running = True
    mode = None
    stage = None
    active_input = True

    while running:
        button_test_mode, button_game_mode,submit_button_obj,stage_buttons = display_menu()
        # stage_buttons = draw_stage_buttons()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_test_mode.collidepoint(event.pos):
                    print("Test Mode Selected")
                    mode = 'test'
                    running = False  # Stop the menu screen to allow stage selection
                elif button_game_mode.collidepoint(event.pos):
                    print("Game Mode Selected")
                    mode = 'game'
                    running = False  # Stop the menu screen to allow stage selection
                if submit_button_obj.collidepoint(event.pos):
                    if mode == 'test':
                        print("Test Mode: Closing the window.")
                        pygame.quit()
                        running = False  # Close the pygame window but not the socket
                    elif mode == 'game':
                        # Send data and close pygame window
                        start_client(mode, stage)
                        pygame.quit()
                        running = False 

            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, stage_button in enumerate(stage_buttons):
                    if stage_button.collidepoint(event.pos):
                        stage = i if mode == 'test' else i + 1  # Adjust for test or game mode
                        print(f"Stage {stage} Selected")
                        running = False  # Stop the stage selection

            if event.type == pygame.KEYDOWN and active_input:
                if event.key == pygame.K_BACKSPACE:
                    team_name = team_name[:-1]  # Remove last character
                elif event.key == pygame.K_RETURN:
                    print(f"Team Name Entered: {team_name}")
                    active_input = False  # Disable further input after pressing Enter
                else:
                    team_name += event.unicode  # Add typed character

        if mode and stage is not None:  # Proceed only if mode and stage are selected
            start_client(mode, stage)


if __name__ == "__main__":
    main()
