import pygame
import sys
from map_drawer import GraphVisualizer
from player import load_player_info

pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 1400, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (30, 100, 150)
BROWN = (88, 44, 44)

# Fonts
pygame.font.init()
FONT = pygame.font.SysFont('Arial', 16)

# Layout Dimensions
BUTTON_WIDTH, BUTTON_HEIGHT = 40, 40
STATUS_PANEL_HEIGHT = 100
HISTORY_PANEL_WIDTH = 600

# Map Dimensions and Position
MAP_X = HISTORY_PANEL_WIDTH
MAP_Y = 0
MAP_WIDTH = SCREEN_WIDTH - HISTORY_PANEL_WIDTH
MAP_HEIGHT = SCREEN_HEIGHT

# Game clock
clock = pygame.time.Clock()

GRAPH_FILE_PATH = "src/ext/map.json"
START_END_PATH = "src/ext/start_end_indices.json"
SETUP_PATH = "src/ext/setup.json"


class GameManager:
    def __init__(self, DrawManager):
        self.GV = DrawManager

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Simulator")

        # Load images for buttons
        self.play_button_image = pygame.image.load('src/imgs/play.png')
        self.pause_button_image = pygame.image.load('src/imgs/pause.png')
        self.stop_button_image = pygame.image.load('src/imgs/stop.png')

        self.play_button_image = pygame.transform.scale(self.play_button_image, (50, 50))
        self.pause_button_image = pygame.transform.scale(self.pause_button_image, (50, 50))
        self.stop_button_image = pygame.transform.scale(self.stop_button_image, (50, 50))

        self.play_button_rect = self.play_button_image.get_rect(topleft=(10, 10))
        self.pause_button_rect = self.pause_button_image.get_rect(topleft=(70, 10))
        self.stop_button_rect = self.stop_button_image.get_rect(topleft=(130, 10))

        # Initialize game state
        self.running = False
        self.time = 0
        self.clock = pygame.time.Clock()
    
    def InitPlayers(self):
        self.players = load_player_info(START_END_PATH, SETUP_PATH, self.GV)
        for player in self.players:
            print(player)

    def UpdatePlayers(self):
        for player in self.players:
            player.update()

    def ResetPlayers(self):
        ''' Move all players back to start. Resets logs to empty.'''
        self.InitPlayers()
        


    def draw_buttons(self):
        self.screen.blit(self.play_button_image, self.play_button_rect)
        self.screen.blit(self.pause_button_image, self.pause_button_rect)
        self.screen.blit(self.stop_button_image, self.stop_button_rect)

    def draw_status_panel(self):
        margin = 10
        padding = 10
        half_padding = 5

        outer_x = margin
        outer_y = 80 + margin
        outer_width = HISTORY_PANEL_WIDTH - 2 * margin
        outer_height = STATUS_PANEL_HEIGHT - 2 * margin

        pygame.draw.rect(screen, GRAY, (outer_x, outer_y, outer_width, outer_height))

        text_x = outer_x + padding
        text_y = outer_y + half_padding

        status_text = FONT.render("Status:", True, BLACK)
        time_text = FONT.render(f"Time since started: {self.time // 1000} sec", True, BLACK)
        completed_text = FONT.render("Number of people completed: X/N", True, BLACK)

        screen.blit(status_text, (text_x, text_y))
        screen.blit(completed_text, (text_x, text_y + 50))

    def draw_report_history(self):
        margin = 10 
        padding = 10

        outer_x = margin
        outer_y = 180 + margin
        outer_width = HISTORY_PANEL_WIDTH - 2 * margin
        outer_height = SCREEN_HEIGHT - 180 - 2 * margin

        pygame.draw.rect(screen, GRAY, (outer_x, outer_y, outer_width, outer_height))

        text_x = outer_x + padding
        text_y = outer_y + padding

        history_text = FONT.render("Report History", True, BLACK)
        screen.blit(history_text, (text_x, text_y))

    def draw_map(self):
        padding = 10
        map_rect = pygame.Rect(MAP_X + padding, MAP_Y + padding, MAP_WIDTH - 2 * padding, MAP_HEIGHT - 2 * padding)
        pygame.draw.rect(screen, BROWN, map_rect)
        self.GV.draw_graph(screen, map_rect)
        self.GV.draw_players(screen, self.players, map_rect)

    def draw_timer(self):
        if self.running:
            self.time += clock.get_time()  # Add time for each frame when running

        timer_text = FONT.render(f"Time: {self.time // 1000} sec", True, BLACK)
        screen.blit(timer_text, (20, 120))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Check for button clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if self.play_button_rect.collidepoint(mouse_pos):
                    if not self.running:
                        self.running = True
                elif self.pause_button_rect.collidepoint(mouse_pos):
                    self.running = False
                elif self.stop_button_rect.collidepoint(mouse_pos):
                    self.running = False
                    self.time = 0  # Reset the time accumulator
                    self.ResetPlayers()

        return True

    def update(self):
        screen.fill(WHITE)

        self.draw_buttons()
        self.draw_status_panel()
        self.draw_report_history()
        self.draw_map()
        self.draw_timer()

        if self.running:
            self.UpdatePlayers()

        return self.handle_events()



def main():
    DrawManager = GraphVisualizer(GRAPH_FILE_PATH)
    game_manager = GameManager(DrawManager)
    game_manager.InitPlayers()

    playing = True 
    while playing:
        playing = game_manager.update()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


# Run the simulation
if __name__ == "__main__":
    main()