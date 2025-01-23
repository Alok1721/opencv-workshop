import pygame
import pygame_widgets
from pygame_widgets.button import Button
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Create a button
button = Button(
    screen,  # The screen surface to draw the button
    350,  # x position of the button
    250,  # y position of the button
    100,  # button width
    50,   # button height
    text="Click Me",  # Button text
    fontSize=30,  # Text size
    margin=10,  # Margin for text inside the button
    inactiveColour=BLUE,  # Button color when not clicked
    activeColour=GREEN,  # Button color when clicked
    hoverColour=(255, 100, 100),  # Color when hovered over
    onClick=lambda: print("Button clicked!")  # Action when button is clicked
)

# Main loop
running = True
while running:
    screen.fill(WHITE)

    # Draw button and handle events
    button.draw()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()
sys.exit()
