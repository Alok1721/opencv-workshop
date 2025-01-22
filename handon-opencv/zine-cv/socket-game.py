import pygame
import sys
import threading
pygame.init()
import components
import server


# Set up display
display_info = pygame.display.Info()
WIDTH, HEIGHT= 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))#, pygame.FULLSCREEN
pygame.display.set_caption("Zine CV")

# Display the new background and scale it to fit the screen
bg = pygame.image.load("back.jpg")
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
screen.blit(bg, (0, 0))
new_data_received = False
teams = []
scores = {}
correct_result = [[1,2],[3,5],[6,7],[5,6]]


'''this will run background thread for server-client connection''' 
threading.Thread(target=server.start_server, args=(teams,scores,correct_result),daemon=True).start()

def draw_main_screen():
    screen.blit(bg, (0, 0))
    title = components.font.render("PARTICIPANTS", True, components.BLUE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
    
    start_y = 150
    for idx, team in enumerate(teams):
        pygame.draw.rect(screen, components.GRAY, (WIDTH // 2 - 150, start_y + idx * 60, 300, 50), border_radius=10)
        text = components.font.render(f"{team} ({scores[team]})", True, components.BLACK)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, start_y + idx * 60 + 10))

    pygame.draw.rect(screen, components.BLACK, (WIDTH // 2 - 102, HEIGHT - 152, 204, 54), border_radius=15)
    pygame.draw.rect(screen, components.BLUE, (WIDTH // 2 - 100, HEIGHT - 150, 200, 50), border_radius=15)
    btn_text = components.font.render("Start Game", True, components.WHITE)
    screen.blit(btn_text, (WIDTH // 2 - btn_text.get_width() // 2, HEIGHT - 140))
    
    pygame.display.flip()

def draw_graph():
    global teams, scores, new_data_received
    users_scores = list(scores.items())
    users_scores.sort(key=lambda x: x[1], reverse=True)
    
    colors = components.graph_colors
    if len(users_scores) == 0:
        no_teams_text = components.font.render("No teams connected to the server", True, components.RED)
        screen.blit(no_teams_text, (WIDTH // 2 - no_teams_text.get_width() // 2, HEIGHT // 2 - no_teams_text.get_height() // 2))
        pygame.display.flip()
        return
    
    screen.blit(bg, (0, 0))
    title = components.font.render("Team Performance", True, components.BLUE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

    bar_width = max(WIDTH // (len(users_scores) * 2), 50)
    spacing = 20
    total_width = len(users_scores) * (bar_width + spacing)
    start_x = (WIDTH - total_width) // 2
    max_score = max([score for _, score in users_scores]) if users_scores else 1  # Avoid division by 0
    scale_factor = (HEIGHT - 300) / max_score if max_score > 0 else 1

    for i, (user, score) in enumerate(users_scores):
        color = colors[i % len(colors)]
        bar_height = score * scale_factor
        pygame.draw.rect(screen, color, (start_x + i * (bar_width + spacing), HEIGHT - bar_height - 150, bar_width, bar_height), border_radius=5)
        label = components.small_font.render(user, True, components.WHITE)
        screen.blit(label, (start_x + i * (bar_width + spacing), HEIGHT - 80))
        score_text = components.small_font.render(str(score), True, components.WHITE)
        screen.blit(score_text, (start_x + i * (bar_width + spacing), HEIGHT - bar_height - 170))

    components.draw_back_button(screen)
    pygame.display.flip()  


def main():
    global new_data_received
    running = True
    in_graph=False
    while running:
        if not in_graph:  
            draw_main_screen()
        else:
            draw_graph()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if WIDTH // 2 - 100 <= x <= WIDTH // 2 + 100 and HEIGHT - 150 <= y <= HEIGHT - 100:
                    in_graph = True
                elif x < 100 and y < 100:
                    in_graph = False
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
