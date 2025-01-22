import os
import importlib
import random
import pygame
import math

class TeamSelector:
    def __init__(self, screen_width, screen_height):
        self.WIDTH = screen_width
        self.HEIGHT = screen_height
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.FPS = 60
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.PRIMARY = (86, 63, 251)
        self.HOVER = (106, 83, 255)
        self.BG_COLOR = (18, 18, 18)
        
        # Fonts
        self.title_font = pygame.font.Font(None, 64)
        self.team_font = pygame.font.Font(None, 36)
        
        # Selection state
        self.team1_selected = None
        self.team2_selected = None
        self.current_selecting = 1  # 1 for player 1, 2 for player 2
        
        # Load teams
        self.teams = self.get_team_scripts()
        self.scroll_offset = 0
        self.max_visible_teams = 8
        self.button_height = 50
        self.button_spacing = 10

    def get_team_scripts(self):
        teams = []
        teams_dir = "teams"
        
        if not os.path.exists(teams_dir):
            print(f"Warning: {teams_dir} directory not found")
            return teams

        for file in os.listdir(teams_dir):
            if file.endswith(".py") and not file.startswith("__"):
                team_name = file[:-3]  # Remove .py extension
                teams.append(team_name)
        
        return sorted(teams)

    def draw_selection_screen(self):
        # Draw gradient background
        for y in range(self.HEIGHT):
            alpha = y / self.HEIGHT
            color = [int(self.BG_COLOR[i] + (self.PRIMARY[i] - self.BG_COLOR[i]) * alpha * 0.15) for i in range(3)]
            pygame.draw.line(self.screen, tuple(color), (0, y), (self.WIDTH, y))

        # Draw title
        title_text = self.title_font.render("Select Teams", True, self.WHITE)
        title_rect = title_text.get_rect(center=(self.WIDTH // 2, 50))
        self.screen.blit(title_text, title_rect)

        # Draw player selection status
        status_text = f"Selecting Player {self.current_selecting}"
        status_surface = self.team_font.render(status_text, True, self.WHITE)
        status_rect = status_surface.get_rect(center=(self.WIDTH // 2, 100))
        self.screen.blit(status_surface, status_rect)

        # Draw team buttons
        button_y = 150
        visible_range = range(
            max(0, self.scroll_offset),
            min(len(self.teams), self.scroll_offset + self.max_visible_teams)
        )

        for i in visible_range:
            team_name = self.teams[i]
            button_rect = pygame.Rect(
                self.WIDTH // 4,
                button_y + (i - self.scroll_offset) * (self.button_height + self.button_spacing),
                self.WIDTH // 2,
                self.button_height
            )
            
            # Check if mouse is hovering over button
            mouse_pos = pygame.mouse.get_pos()
            is_hovered = button_rect.collidepoint(mouse_pos)
            is_selected = (team_name == self.team1_selected or team_name == self.team2_selected)
            
            # Draw button with appropriate color
            button_color = self.HOVER if is_hovered else self.PRIMARY
            if is_selected:
                button_color = (0, 255, 0)  # Green for selected
                
            pygame.draw.rect(self.screen, button_color, button_rect, border_radius=10)
            
            # Draw team name
            team_text = self.team_font.render(team_name, True, self.WHITE)
            text_rect = team_text.get_rect(center=button_rect.center)
            self.screen.blit(team_text, text_rect)

        # Draw scroll indicators if needed
        if len(self.teams) > self.max_visible_teams:
            if self.scroll_offset > 0:
                pygame.draw.polygon(self.screen, self.WHITE, [
                    (self.WIDTH // 2, 140),
                    (self.WIDTH // 2 - 10, 130),
                    (self.WIDTH // 2 + 10, 130)
                ])
            if self.scroll_offset + self.max_visible_teams < len(self.teams):
                bottom_y = 150 + (self.max_visible_teams * (self.button_height + self.button_spacing))
                pygame.draw.polygon(self.screen, self.WHITE, [
                    (self.WIDTH // 2, bottom_y + 20),
                    (self.WIDTH // 2 - 10, bottom_y + 10),
                    (self.WIDTH // 2 + 10, bottom_y + 10)
                ])

        # Draw selected teams
        if self.team1_selected:
            text = f"Player 1: {self.team1_selected}"
            surface = self.team_font.render(text, True, self.WHITE)
            self.screen.blit(surface, (20, self.HEIGHT - 60))
        
        if self.team2_selected:
            text = f"Player 2: {self.team2_selected}"
            surface = self.team_font.render(text, True, self.WHITE)
            self.screen.blit(surface, (20, self.HEIGHT - 30))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, None, None
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check team button clicks
                    button_y = 150
                    visible_range = range(
                        max(0, self.scroll_offset),
                        min(len(self.teams), self.scroll_offset + self.max_visible_teams)
                    )
                    
                    for i in visible_range:
                        button_rect = pygame.Rect(
                            self.WIDTH // 4,
                            button_y + (i - self.scroll_offset) * (self.button_height + self.button_spacing),
                            self.WIDTH // 2,
                            self.button_height
                        )
                        
                        if button_rect.collidepoint(event.pos):
                            selected_team = self.teams[i]
                            if self.current_selecting == 1:
                                self.team1_selected = selected_team
                                self.current_selecting = 2
                            else:
                                if selected_team != self.team1_selected:  # Prevent selecting same team
                                    self.team2_selected = selected_team
                                    # Both teams selected, load and return
                                    return self.load_team_scripts()
                
                elif event.button == 4:  # Mouse wheel up
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                elif event.button == 5:  # Mouse wheel down
                    self.scroll_offset = min(
                        len(self.teams) - self.max_visible_teams,
                        self.scroll_offset + 1
                    )
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.current_selecting == 2 and self.team1_selected:
                        self.team1_selected = None
                        self.current_selecting = 1
                    elif self.current_selecting == 2 and self.team2_selected:
                        self.team2_selected = None
        
        return True, None, None

    def load_team_scripts(self):
        try:
            # Import the selected team scripts
            team1_module = importlib.import_module(f"teams.{self.team1_selected}")
            team2_module = importlib.import_module(f"teams.{self.team2_selected}")
            
            return False, team1_module.player_script, team2_module.player_script
        except Exception as e:
            print(f"Error loading team scripts: {e}")
            return True, None, None

    def run(self):
        running = True
        while running:
            self.screen.fill(self.BG_COLOR)
            self.draw_selection_screen()
            running, script1, script2 = self.handle_events()
            
            if script1 and script2:
                return script1, script2
            
            pygame.display.flip()
            self.clock.tick(self.FPS)
        
        return None, None

class FootballGame:
    def __init__(self):
        pygame.init()
        self.WIDTH = 800
        self.HEIGHT = 600
        
        # Create team selector and get selected teams
        selector = TeamSelector(self.WIDTH, self.HEIGHT)
        player_script_left, player_script_right = selector.run()
        
        if player_script_left is None or player_script_right is None:
            raise SystemExit("Team selection cancelled")
            
        # Initialize the rest of the game with selected teams
        self.init_game(player_script_left, player_script_right)

    def init_game(self, player_script_left, player_script_right):
        # Initialize pygame
        pygame.init()
        
        # Screen settings
        self.WIDTH = 800
        self.HEIGHT = 600
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Turn-Based Football Game")
        
        # Load and prepare cannon sprites
        self.cannon1_img = pygame.image.load("cannon.png")
        self.cannon2_img = pygame.image.load("cannon.png")
        self.cannon1_img = pygame.transform.scale(self.cannon1_img, (60, 20))
        self.cannon2_img = pygame.transform.scale(self.cannon2_img, (60, 20))
        self.cannon2_img = pygame.transform.flip(self.cannon2_img, False, True)
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        self.GREEN = (0, 255, 0)
        self.GRAY = (200, 200, 200)
        
        # Clock settings
        self.game_time = 60
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.counter = self.game_time
        pygame.time.set_timer(pygame.USEREVENT, 1000)
        
        # Ball settings
        self.BALL_RADIUS = 20
        self.positions = [(self.WIDTH // 2, self.HEIGHT // 2),
                         (self.WIDTH // 2, self.HEIGHT // 2 + 50),
                         (self.WIDTH // 2, self.HEIGHT // 2 - 50),
                         (self.WIDTH // 2, self.HEIGHT // 2 + 100),
                         (self.WIDTH // 2 - 50, self.HEIGHT // 2 - 100)]
        self.ball_pos = [self.WIDTH // 2, self.HEIGHT // 2]
        self.ball_vel = [0, 0]
        self.FRICTION = 0.995
        
        # Cannon settings
        self.cannon1_pos = (50, self.HEIGHT // 2)
        self.cannon2_pos = (self.WIDTH - 50, self.HEIGHT // 2)
        self.CANNON_RADIUS = 30
        self.BULLET_RADIUS = 5
        self.MAX_POWER = 30
        self.BULLET_SPEED = 15
        self.power_increment = 0.13
        
        # Game state
        self.cannon1_angle = 45
        self.cannon2_angle = 45
        self.cannon1_power = 0
        self.cannon2_power = 0
        self.bullets = []
        self.angle1 = 0
        self.angle2 = 180
        
        # Bullet counts
        self.powerbulletscount = 5
        self.precisionbulletscount = 10
        self.powerbullets1 = self.powerbulletscount
        self.powerbullets2 = self.powerbulletscount
        self.precisionbullets1 = self.precisionbulletscount
        self.precisionbullets2 = self.precisionbulletscount
        self.bullets_used1 = 0
        self.bullets_used2 = 0
        
        # Bullet parameters
        self.powerbullet_angle_error = 5
        self.powerbullet_multiplier = 1.5
        
        # Score and winning conditions
        self.player1_score = 0
        self.player2_score = 0
        self.winning_score = 1
        
        # Turn management
        self.turn_delay = 0.6
        self.player1_ready = False
        self.player2_ready = False
        self.last_shot_time1 = 0
        self.last_shot_time2 = 0
        self.player1_executing = None
        self.player2_executing = None
        
        # Font initialization
        self.font = pygame.font.Font(None, 36)
        self.font_bulletcount = pygame.font.Font(None, 24)
        
        # Player scripts
        self.player_script_left = player_script_left
        self.player_script_right = player_script_right
        
        # Game state
        self.running = True
        self.game_over = False
        self.round_counter = 0

    def draw_field(self):
        self.screen.fill((34, 139, 34))
        pygame.draw.rect(self.screen, self.WHITE, (50, 50, self.WIDTH - 100, self.HEIGHT - 100), 5)
        pygame.draw.line(self.screen, self.WHITE, (self.WIDTH // 2, 50), (self.WIDTH // 2, self.HEIGHT - 50), 5)
        pygame.draw.circle(self.screen, self.WHITE, (self.WIDTH // 2, self.HEIGHT // 2), 70, 5)
        pygame.draw.rect(self.screen, self.WHITE, (50, self.HEIGHT // 2 - 75, 50, 150), 5)
        pygame.draw.rect(self.screen, self.WHITE, (self.WIDTH - 100, self.HEIGHT // 2 - 75, 50, 150), 5)

    def draw_cannon(self, x, y, img, angle):
        rotated_img = pygame.transform.rotate(img, angle)
        img_rect = rotated_img.get_rect(center=(x, y))
        self.screen.blit(rotated_img, img_rect.topleft)
        return angle

    def draw_power_bar(self, x, y, power, color):
        pygame.draw.rect(self.screen, self.GRAY, (x - 25, y + 40, 50, 10))
        pygame.draw.rect(self.screen, color, (x - 25, y + 40, int(50 * (power / self.MAX_POWER)), 10))

    def draw_ball(self):
        pygame.draw.circle(self.screen, self.GREEN, self.ball_pos, self.BALL_RADIUS)

    def draw_bullets(self):
        for bullet in self.bullets:
            color = self.RED if bullet[4] == "power" else self.BLACK
            pygame.draw.circle(self.screen, color, (int(bullet[0]), int(bullet[1])), self.BULLET_RADIUS)

    def update_ball(self):
        self.ball_pos[0] += self.ball_vel[0]
        self.ball_pos[1] += self.ball_vel[1]
        
        self.ball_vel[0] *= self.FRICTION
        self.ball_vel[1] *= self.FRICTION
        
        if abs(self.ball_vel[0]) < 0.1:
            self.ball_vel[0] = 0
        if abs(self.ball_vel[1]) < 0.1:
            self.ball_vel[1] = 0
            
        if self.ball_pos[1] - self.BALL_RADIUS <= 0 or self.ball_pos[1] + self.BALL_RADIUS >= self.HEIGHT:
            self.ball_vel[1] = -self.ball_vel[1]
        if self.ball_pos[0] - self.BALL_RADIUS <= 0:
            self.player2_score += 1
            self.reset_ball()
        elif self.ball_pos[0] + self.BALL_RADIUS >= self.WIDTH:
            self.player1_score += 1
            self.reset_ball()

    def reset_ball(self):
        self.round_counter += 1
        self.ball_pos[:] = [self.positions[self.round_counter % 5][0] + random.randint(-5, 5),
                           self.positions[self.round_counter % 5][1] + random.randint(-5, 5)]
        self.ball_vel[:] = [0, 0]
        self.powerbullets1 = self.powerbulletscount
        self.powerbullets2 = self.powerbulletscount
        self.precisionbullets1 = self.precisionbulletscount
        self.precisionbullets2 = self.precisionbulletscount
        self.bullets.clear()
        self.player1_executing = None
        self.player2_executing = None
        self.cannon1_power = 0
        self.cannon2_power = 0

    def handle_bullets(self):
        for bullet in self.bullets[:]:
            bullet[0] += math.cos(math.radians(bullet[2])) * self.BULLET_SPEED
            bullet[1] -= math.sin(math.radians(bullet[2])) * self.BULLET_SPEED
            
            if (bullet[0] < 0 or bullet[0] > self.WIDTH or
                    bullet[1] < 0 or bullet[1] > self.HEIGHT):
                self.bullets.remove(bullet)
                continue
            
            dist = math.hypot(bullet[0] - self.ball_pos[0], bullet[1] - self.ball_pos[1])
            if dist <= self.BALL_RADIUS + self.BULLET_RADIUS:
                angle = math.atan2(self.ball_pos[1] - bullet[1], self.ball_pos[0] - bullet[0])
                multiplier = self.powerbullet_multiplier if bullet[4] == "power" else 1
                self.ball_vel[0] += math.cos(angle) * bullet[3] * self.power_increment * multiplier
                self.ball_vel[1] += math.sin(angle) * bullet[3] * self.power_increment * multiplier
                self.bullets.remove(bullet)

    def restart_game(self):
        self.round_counter = 0
        self.bullets_used1 = 0
        self.bullets_used2 = 0
        self.counter = self.game_time
        self.player1_score = 0
        self.player2_score = 0
        self.reset_ball()

    def draw_game_over_screen(self):
        # Implement game over screen drawing logic here
        # (Previous game over screen implementation)
        pass

    def handle_game_over_events(self, event, restart_button):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if restart_button.collidepoint(event.pos):
                return True
        return False

    def run(self):
        while self.running:
            if self.game_over:
                restart_button = self.draw_game_over_screen()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        self.game_over = False
                    if self.handle_game_over_events(event, restart_button):
                        self.game_over = False
                        self.restart_game()
                
                pygame.display.flip()
                self.clock.tick(self.FPS)
                continue

            self.draw_field()
            self.cannon1_angle = self.draw_cannon(50, self.HEIGHT // 2, self.cannon1_img, self.angle1)
            self.cannon2_angle = self.draw_cannon(self.WIDTH - 50, self.HEIGHT // 2, self.cannon2_img, self.angle2)
            self.draw_ball()
            self.draw_bullets()
            self.draw_power_bar(50, self.HEIGHT // 2, self.cannon1_power, self.RED)
            self.draw_power_bar(self.WIDTH - 50, self.HEIGHT // 2, self.cannon2_power, self.BLUE)

            current_time = pygame.time.get_ticks()
            
            # Handle player turns and script execution
            self.handle_player_turns(current_time)
            
            # Handle events and update game state
            self.handle_events()
            
            # Update game elements
            self.update_ball()
            self.handle_bullets()
            
            # Draw UI elements
            self.draw_ui()
            
            pygame.display.flip()
            self.clock.tick(self.FPS)

        pygame.quit()

    def handle_player_turns(self, current_time):
        # Update player readiness
        self.player1_ready = current_time - self.last_shot_time1 >= self.turn_delay * 1000
        self.player2_ready = current_time - self.last_shot_time2 >= self.turn_delay * 1000
        
        # Handle player 1 execution
        if self.player1_executing is not None:
            self.execute_player1_shot()
        elif self.player1_ready:
            self.handle_player1_command()
            
        # Handle player 2 execution
        if self.player2_executing is not None:
            self.execute_player2_shot()
        elif self.player2_ready:
            self.handle_player2_command()

    def execute_player1_shot(self):
        if self.cannon1_power < self.player1_executing[1] and self.cannon1_power < self.MAX_POWER:
            self.cannon1_power += 1
        else:
            angle = self.player1_executing[0]
            if self.player1_executing[2] == "power":
                angle += random.uniform(-self.powerbullet_angle_error, self.powerbullet_angle_error)
            self.bullets.append([50, self.HEIGHT // 2, angle, self.cannon1_power, self.player1_executing[2]])
            self.last_shot_time1 = pygame.time.get_ticks()
            self.cannon1_power = 0
            self.player1_executing = None

    def handle_player1_command(self):
        player1_command = self.player_script_left(self.cannon1_pos, self.ball_pos, 
                                                self.powerbullets1, self.precisionbullets1, 
                                                self.ball_vel)
        if player1_command is not None:
            angle, power, bullet_type = player1_command
            self.angle1 = angle
            if self.process_player_shot(1, angle, power, bullet_type):
                self.player1_ready = False

    def execute_player2_shot(self):
        if self.cannon2_power < self.player2_executing[1] and self.cannon2_power < self.MAX_POWER:
            self.cannon2_power += 1
        else:
            self.bullets.append([self.WIDTH - 50, self.HEIGHT // 2, 
                               self.player2_executing[0], self.cannon2_power, 
                               self.player2_executing[2]])
            self.last_shot_time2 = pygame.time.get_ticks()
            self.cannon2_power = 0
            self.player2_executing = None

    def handle_player2_command(self):
        player2_command = self.player_script_right(self.cannon2_pos, self.ball_pos,
                                                 self.powerbullets2, self.precisionbullets2,
                                                 self.ball_vel)
        if player2_command is not None:
            angle, power, bullet_type = player2_command
            self.angle2 = angle
            if self.process_player_shot(2, angle, power, bullet_type):
                self.player2_ready = False

    def process_player_shot(self, player, angle, power, bullet_type):
        if player == 1:
            if bullet_type == "power" and self.powerbullets1 > 0:
                self.player1_executing = (angle, power, bullet_type)
                self.powerbullets1 -= 1
                self.bullets_used1 += 1
                return True
            elif bullet_type == "precision" and self.precisionbullets1 > 0:
                self.player1_executing = (angle, power, bullet_type)
                self.precisionbullets1 -= 1
                self.bullets_used1 += 1
                return True
        else:
            if bullet_type == "power" and self.powerbullets2 > 0:
                self.player2_executing = (angle, power, bullet_type)
                self.powerbullets2 -= 1
                self.bullets_used2 += 1
                return True
            elif bullet_type == "precision" and self.precisionbullets2 > 0:
                self.player2_executing = (angle, power, bullet_type)
                self.precisionbullets2 -= 1
                self.bullets_used2 += 1
                return True
        return False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.USEREVENT:
                self.counter -= 1
                if self.counter <= 0:
                    self.game_over = True

        # Check for game-ending conditions
        if self.player1_score >= self.winning_score or self.player2_score >= self.winning_score:
            self.game_over = True

        # Check if ball is not moving and both players are out of bullets
        if (self.ball_vel[0] == 0 and self.ball_vel[1] == 0 and 
            self.powerbullets1 == 0 and self.powerbullets2 == 0 and 
            self.precisionbullets1 == 0 and self.precisionbullets2 == 0):
            if abs(self.ball_pos[0] - self.cannon1_pos[0]) > abs(self.ball_pos[0] - self.cannon2_pos[0]):
                self.player1_score += 1
            else:
                self.player2_score += 1
            self.reset_ball()

    def draw_ui(self):
        # Draw scores
        score_text = self.font.render(
            f"Player 1: {self.player1_score}  Player 2: {self.player2_score}", 
            True, self.BLACK
        )
        self.screen.blit(score_text, (self.WIDTH // 2 - score_text.get_width() // 2, 10))
        
        # Draw timer
        timer_text = self.font.render(f"Time: {self.counter}", True, self.BLACK)
        self.screen.blit(timer_text, (self.WIDTH // 2 - 50, 100))
        
        # Draw bullet counts for Player 1
        power_text1 = self.font_bulletcount.render(f"Power Bullets: {self.powerbullets1}", True, self.BLACK)
        precision_text1 = self.font_bulletcount.render(f"Precision Bullets: {self.precisionbullets1}", True, self.BLACK)
        
        self.screen.blit(power_text1, (10, self.HEIGHT - power_text1.get_height() - 10))
        self.screen.blit(precision_text1, (10, self.HEIGHT - power_text1.get_height() - 
                                         precision_text1.get_height() - 20))
        
        # Draw bullet counts for Player 2
        power_text2 = self.font_bulletcount.render(f"Power Bullets: {self.powerbullets2}", True, self.BLACK)
        precision_text2 = self.font_bulletcount.render(f"Precision Bullets: {self.precisionbullets2}", True, self.BLACK)
        
        self.screen.blit(power_text2, (self.WIDTH - power_text2.get_width() - 10, 
                                     self.HEIGHT - power_text2.get_height() - 10))
        self.screen.blit(precision_text2, (self.WIDTH - precision_text2.get_width() - 10,
                                         self.HEIGHT - power_text2.get_height() - 
                                         precision_text2.get_height() - 20))
        
        # Draw FPS counter
        fps_text = self.font.render(f"FPS: {int(self.clock.get_fps())}", True, self.WHITE)
        self.screen.blit(fps_text, (10, 10))

    def draw_game_over_screen(self):
        # Modern color palette
        BG_COLOR = (18, 18, 18)
        PRIMARY = (86, 63, 251)
        WHITE = (255, 255, 255)
        GRAY = (130, 130, 130)
        
        # Create background with subtle gradient
        background = pygame.Surface((self.WIDTH, self.HEIGHT))
        for y in range(self.HEIGHT):
            alpha = y / self.HEIGHT
            color = [int(BG_COLOR[i] + (PRIMARY[i] - BG_COLOR[i]) * alpha * 0.15) for i in range(3)]
            pygame.draw.line(background, tuple(color), (0, y), (self.WIDTH, y))
        self.screen.blit(background, (0, 0))
        
        # Determine winner
        if self.player1_score > self.player2_score:
            winner = 1
        elif self.player2_score > self.player1_score:
            winner = 2
        else:
            winner = 1 if self.bullets_used1 < self.bullets_used2 else 2
            
        # Draw score cards
        self.draw_score_card(1, self.player1_score, self.bullets_used1, self.WIDTH//4 - 140, self.HEIGHT//3)
        self.draw_score_card(2, self.player2_score, self.bullets_used2, self.WIDTH*3//4 - 140, self.HEIGHT//3)
        
        # Draw winner announcement
        winner_font = pygame.font.Font(None, 84)
        winner_text = f"PLAYER {winner} WINS!"
        winner_surface = winner_font.render(winner_text, True, WHITE)
        winner_rect = winner_surface.get_rect(center=(self.WIDTH//2, self.HEIGHT//4))
        self.screen.blit(winner_surface, winner_rect)
        
        # Create restart button
        button_width = 240
        button_height = 60
        button_x = self.WIDTH//2 - button_width//2
        button_y = self.HEIGHT*3//4 - button_height//2
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        
        # Draw button
        pygame.draw.rect(self.screen, PRIMARY, button_rect, border_radius=15)
        button_text = self.font.render("PLAY AGAIN", True, WHITE)
        text_rect = button_text.get_rect(center=button_rect.center)
        self.screen.blit(button_text, text_rect)
        
        return button_rect

    def draw_score_card(self, player_num, score, bullets, x, y):
        PRIMARY = (86, 63, 251)
        WHITE = (255, 255, 255)
        GRAY = (130, 130, 130)
        
        card_width = 280
        card_height = 150
        card_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
        
        # Card background
        pygame.draw.rect(card_surface, (*PRIMARY, 40), (0, 0, card_width, card_height), border_radius=15)
        
        # Player text
        player_font = pygame.font.Font(None, 36)
        player_text = player_font.render(f"PLAYER {player_num}", True, WHITE)
        card_surface.blit(player_text, (20, 20))
        
        # Score
        score_font = pygame.font.Font(None, 72)
        score_text = score_font.render(str(score), True, WHITE)
        card_surface.blit(score_text, (20, 50))
        
        # Bullets used
        bullets_font = pygame.font.Font(None, 28)
        bullets_text = bullets_font.render(f"Bullets: {bullets}", True, GRAY)
        card_surface.blit(bullets_text, (20, 110))
        
        # Apply floating animation
        current_time = pygame.time.get_ticks()
        y_offset = math.sin(current_time / 1000 * 2 + (player_num * math.pi)) * 5
        self.screen.blit(card_surface, (x, y + y_offset))

# Example usage
def main():
    try:
        game = FootballGame()
        game.run()
    except SystemExit as e:
        print(e)
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()