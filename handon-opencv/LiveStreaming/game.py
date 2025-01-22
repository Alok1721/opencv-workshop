import pygame
import random
import sys
import time

# Initialize pygame
pygame.init()

# Set up display
display_info = pygame.display.Info()
# WIDTH, HEIGHT = display_info.current_w, display_info.current_h
WIDTH, HEIGHT= 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))#, pygame.FULLSCREEN
pygame.display.set_caption("Team Selection")

# Display the new background and scale it to fit the screen
bg = pygame.image.load("back.jpg")
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
screen.blit(bg, (0, 0))

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 102, 204)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (200, 200, 200)

# Fonts
font = pygame.font.Font(None, 50)
small_font = pygame.font.Font(None, 36)

# Team names
teams = ["Team A", "Team B", "Team C", "Team D", "Team E",]

def draw_main_screen():
    screen.blit(bg, (0, 0))
    title = font.render("Select Your Team", True, BLUE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
    
    # Dynamically position team names with bordered rectangles
    start_y = 150
    for idx, team in enumerate(teams):
        pygame.draw.rect(screen, GRAY, (WIDTH // 2 - 150, start_y + idx * 60, 300, 50), border_radius=10)
        text = font.render(team, True, BLACK)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, start_y + idx * 60 + 10))
    
    # Draw Start Game button with shadow
    pygame.draw.rect(screen, BLACK, (WIDTH // 2 - 102, HEIGHT - 152, 204, 54), border_radius=15)
    pygame.draw.rect(screen, BLUE, (WIDTH // 2 - 100, HEIGHT - 150, 200, 50), border_radius=15)
    btn_text = font.render("Start Game", True, WHITE)
    screen.blit(btn_text, (WIDTH // 2 - btn_text.get_width() // 2, HEIGHT - 140))
    
    pygame.display.flip()

def draw_graph():
    global teams
    users = [i for i in teams]
    colors = [BLUE, GREEN, RED, ORANGE]
    
    running = True
    while running:
        screen.blit(bg, (0, 0))
        title = font.render("User Performance", True, BLUE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        scores = [random.randint(50, 150) for _ in users]
        users_scores = list(zip(users, scores))
        users_scores.sort(key=lambda x: x[1], reverse=True)
        
        bar_width = max(WIDTH // (len(users_scores) * 2), 50)
        spacing = 20
        total_width = len(users_scores) * (bar_width + spacing)
        start_x = (WIDTH - total_width) // 2
        max_score = max(scores)
        scale_factor = (HEIGHT - 300) / max_score
        
        for i, (user, score) in enumerate(users_scores):
            color = colors[i % len(colors)]
            bar_height = score * scale_factor
            pygame.draw.rect(screen, color, (start_x + i * (bar_width + spacing), HEIGHT - bar_height - 150, bar_width, bar_height), border_radius=5)
            label = pygame.transform.rotate(small_font.render(user, True, WHITE), 45)
            screen.blit(label, (start_x + i * (bar_width + spacing), HEIGHT - 80))
            score_text = small_font.render(str(score), True, WHITE)
            screen.blit(score_text, (start_x + i * (bar_width + spacing), HEIGHT - bar_height - 170))
        
        pygame.display.flip()
        time.sleep(3)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                running = False  # Return to the main screen

def main():
    running = True
    while running:
        draw_main_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if WIDTH // 2 - 100 <= x <= WIDTH // 2 + 100 and HEIGHT - 150 <= y <= HEIGHT - 100:
                    draw_graph()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
