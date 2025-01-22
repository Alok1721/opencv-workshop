import pygame
pygame.init()

'some components and functions that can be used in the main program'


RED = (255, 12, 12)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (200, 200, 200)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
PINK = (255, 192, 203)
LIME = (0, 255, 0)
BROWN = (165, 42, 42)
MAROON = (128, 0, 0)
OLIVE = (128, 128, 0)
BLUE = (0, 102, 204)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

graph_colors = [ GREEN, RED, ORANGE, CYAN, MAGENTA, YELLOW, PURPLE, PINK, LIME, BROWN, MAROON, OLIVE]

font = pygame.font.Font(None, 50)
small_font = pygame.font.Font(None, 36)


def draw_back_button(screen):
    # Draw the blue rectangle (Back button)
    pygame.draw.rect(screen, BLUE, (12, 12, 60, 50), border_radius=15)
    # Draw a simple left-pointing triangle (Back icon)
    # The triangle will be placed on the left side of the rectangle
    triangle_points = [(12 + 10, 12 + 25), (12 + 30, 12 + 10), (12 + 30, 12 + 40)]
    pygame.draw.polygon(screen, WHITE, triangle_points)
    
    pygame.display.flip()