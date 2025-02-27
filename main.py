from datetime import datetime
import pygame
import sys
from GraphVisualizer import GraphVisualizer
from GameGenerator import GameGenerator
from settings_utils import merge_settings, process_settings, load_settings
from player import LoadPlayerInfo, Player
from roadblock import LoadRoadblockInfo
from congestion import LoadCongestionInfo

import cProfile


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
SETUP_PATH = "src/ext/Setup.json"
DEFAULT_SETUP = "src/ext/DefaultConfig.json"
ROADBLOCK_PATH = "src/ext/roadblock.json"
CONGESTION_PATH = "src/ext/congestion.json"


class GameManager:
    def __init__(self, DrawManager):
        self.GV = DrawManager

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Simulator")

        # Load images for buttons
        self.images = {
            'play': pygame.image.load('src/imgs/play.png').convert_alpha(),
            'pause': pygame.image.load('src/imgs/pause.png').convert_alpha(),
            'stop': pygame.image.load('src/imgs/stop.png').convert_alpha(),
            'save': pygame.image.load('src/imgs/save.png').convert_alpha(),
        }

        # Resize the images
        self.images['play'] = pygame.transform.scale(self.images['play'], (50, 50))
        self.images['pause'] = pygame.transform.scale(self.images['pause'], (50, 50))
        self.images['stop'] = pygame.transform.scale(self.images['stop'], (50, 50))
        self.images['save'] = pygame.transform.scale(self.images['save'], (50, 50))

        # Define button positions
        self.play_button_rect = self.images['play'].get_rect(topleft=(10, 10))
        self.pause_button_rect = self.images['pause'].get_rect(topleft=(70, 10))
        self.stop_button_rect = self.images['stop'].get_rect(topleft=(130, 10))
        self.save_button_rect = self.images['save'].get_rect(topleft=(190, 10))

        # Initialize game state
        self.running = False
        self.time = 0
        self.clock = pygame.time.Clock()

        # Game Related information
        self.num_players = 0
        self.num_completed = 0
        self.time_started = datetime.now().strftime("%m%d_%H%M%S")

        self.selected_player: Player | None = None

    def InitGenerator(self):
        self.Generator = SetupGenerator()
        self.Generator.SaveDecisionCsv(self.time_started)
        self.Generator.SaveSetupCsv(self.time_started)
        self.Generator.SavePlayerDecisionCsv(self.time_started)

    def ResetGenerator(self):
        self.Generator = None 
        self.InitGenerator()
    
    def InitPlayers(self):
        self.players = []
        self.players = LoadPlayerInfo(START_END_PATH, self.time_started, self.GV, self.Generator)
        self.num_players = len(self.players)
        self.finished_players = []

    def UpdatePlayers(self):
        self.finished_players = [player for player in self.players if player.finished]
        unfinished_players = [player for player in self.players if not player.finished] 
        for player in unfinished_players:
            player.update()
            if player.finished:
                self.num_completed += 1
                self.finished_players.append(player)

    def ResetPlayers(self):
        ''' Move all players back to start. Resets position logs to empty.'''
        self.time_started = datetime.now().strftime("%m%d_%H%M%S")
        self.num_completed = 0
        self.finished_players.clear()
        self.num_players = 0
        self.players.clear()
        self.InitPlayers()

    def get_clicked_player(self, mouse_pos) -> Player:
        for player in self.players:
            player_pos = player.pos
            player_rect = pygame.Rect(player_pos[0] - 5, player_pos[1] - 5, 10, 10)

            if player_rect.collidepoint(mouse_pos):
                return player
        return None

    def InitRoadblocks(self):
        """ Spawns Roadblocks from roadblock.json file """
        self.roadblocks = LoadRoadblockInfo(ROADBLOCK_PATH, self.GV)
    
    def ResetRoadblocks(self):
        """ Mark all roadblocks as unreported. """
        self.InitRoadblocks()

    def InitCongestions(self):
        """ Spawns Congestions from congestion.json file"""
        self.congestions = LoadCongestionInfo(CONGESTION_PATH, self.GV)
    
    def ResetCongestions(self):
        """ Rereads the file for congestions."""
        self.InitCongestions()


    def draw_buttons(self):
        self.screen.blit(self.images['play'], self.play_button_rect)
        self.screen.blit(self.images['pause'], self.pause_button_rect)
        self.screen.blit(self.images['stop'], self.stop_button_rect)
        self.screen.blit(self.images['save'], self.save_button_rect)

    def draw_status_panel(self):
        margin = 10
        padding = 10
        half_padding = 5

        outer_x = margin
        outer_y = 80 + margin
        outer_width = (HISTORY_PANEL_WIDTH/ 2) - 2 * margin
        outer_height = STATUS_PANEL_HEIGHT - 2 * margin

        pygame.draw.rect(screen, GRAY, (outer_x, outer_y, outer_width, outer_height))

        text_x = outer_x + padding
        text_y = outer_y + half_padding

        status_text = FONT.render("Status:", True, BLACK)
        time_text = FONT.render(f"Time since started: {self.time // 1000} sec", True, BLACK)
        completed_text = FONT.render(f"Number of people completed: {self.num_completed}/{self.num_players}", True, BLACK)

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

    def draw_target_player(self):
        '''If a player is picked, it will display information about them.'''
        margin = 10
        padding = 10
        half_padding = 5

        outer_x = margin + (HISTORY_PANEL_WIDTH / 2)
        outer_y = 80 + margin - (STATUS_PANEL_HEIGHT - 2 * margin)
        outer_width = (HISTORY_PANEL_WIDTH/ 2) - 2 * margin
        outer_height = (STATUS_PANEL_HEIGHT - 2 * margin) * 2

        pygame.draw.rect(screen, GRAY, (outer_x, outer_y, outer_width, outer_height))

        text_x = outer_x + padding
        text_y = outer_y + half_padding

        follow_player_text = "Following Player:"
        speed_text = "Speed:"
        dest_node_text = "End:"
        next_nav_text = "Next Follows Nav:"
        next_report_roadblock_text = "Next Report Roadblock:"
        next_report_no_roadblock_text = "Next Report No Roadblock:"
        if self.selected_player:
            follow_player_text += f" {self.selected_player.id}"
            speed_text += f" {self.selected_player.speed}"
            dest_node_text += f" {self.selected_player.end}"
            # All information for player decisions
            player_data = self.selected_player.Gen.Players[self.selected_player.id]

            next_nav_idx = player_data["follows_navigation_idx"]
            if next_nav_idx < len(player_data["follows_navigation"]):
                next_nav_text += f" {player_data['follows_navigation'][next_nav_idx]}"

            next_report_roadblock_idx = player_data["reports_roadblock_if_roadblock_idx"]
            if next_report_roadblock_idx < len(player_data["reports_roadblock_if_roadblock"]):
                next_report_roadblock_text += f" {player_data['reports_roadblock_if_roadblock'][next_report_roadblock_idx]}"

            next_report_no_roadblock_idx = player_data["reports_roadblock_no_roadblock_idx"]
            if next_report_no_roadblock_idx < len(player_data["reports_roadblock_no_roadblock"]):
                next_report_no_roadblock_text += f" {player_data['reports_roadblock_no_roadblock'][next_report_no_roadblock_idx]}" 

        follow_player = FONT.render(follow_player_text, True, BLACK)
        player_speed = FONT.render(speed_text, True, BLACK)
        dest_node = FONT.render(dest_node_text, True, BLACK)
        next_nav = FONT.render(next_nav_text, True, BLACK)
        next_report_roadblock = FONT.render(next_report_roadblock_text, True, BLACK)
        next_report_no_roadblock = FONT.render(next_report_no_roadblock_text, True, BLACK)

        screen.blit(follow_player, (text_x, text_y))
        screen.blit(player_speed, (text_x, text_y + 25))
        screen.blit(dest_node, (text_x, text_y + 50))
        screen.blit(next_nav, (text_x, text_y + 75))
        screen.blit(next_report_roadblock, (text_x, text_y + 100))
        screen.blit(next_report_no_roadblock, (text_x, text_y + 125))

    def draw_map(self):
        padding = 10
        map_rect = pygame.Rect(MAP_X + padding, MAP_Y + padding, MAP_WIDTH - 2 * padding, MAP_HEIGHT - 2 * padding)
        pygame.draw.rect(screen, BROWN, map_rect)
        # Add any extra drawing here (Order Matters!)
        if self.selected_player:
            self.GV.draw_player_path(screen, self.selected_player, map_rect)
        self.GV.draw_graph(screen, map_rect)
        self.GV.draw_roadblocks(screen, self.roadblocks, map_rect, self.selected_player)
        self.GV.draw_players(screen, self.players, map_rect)

    def draw_timer(self):
        if self.running:
            self.time += clock.get_time()  # Add time for each frame when running

        timer_text = FONT.render(f"Time: {self.time // 1000} sec", True, BLACK)
        screen.blit(timer_text, (20, 120))

    def save_csv_files(self):
        self.Generator.SaveNavHistory(self.time_started)
        # self.Generator.SaveReportHistory(self.time_started)


    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Check for button clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                for rect, player in self.GV.player_rects:
                    if rect.collidepoint(mouse_pos):
                        if self.selected_player == player:
                            self.selected_player = None
                        else: 
                            self.selected_player = player
                        return True # informs that game is running but can exit function early

                if self.play_button_rect.collidepoint(mouse_pos):
                    if not self.running:
                        self.running = True
                elif self.pause_button_rect.collidepoint(mouse_pos):
                    self.running = False
                elif self.stop_button_rect.collidepoint(mouse_pos):
                    self.save_csv_files()                    
                    self.running = False
                    self.time = 0  # Reset the time accumulator
                    self.ResetGenerator()
                    self.ResetPlayers()
                    self.ResetRoadblocks()
                    self.ResetCongestions()
                    self.selected_player = None
                elif self.save_button_rect.collidepoint(mouse_pos):
                    self.save_csv_files()
        return True

    def update(self):
        screen.fill(WHITE)

        self.draw_buttons()
        self.draw_status_panel()
        self.draw_report_history()
        self.draw_target_player()
        self.draw_map()
        self.draw_timer()

        if self.running:
            self.UpdatePlayers()

        return self.handle_events()
    

def SetupGenerator() -> GameGenerator:
    settings = merge_settings(SETUP_PATH, DEFAULT_SETUP)
    merged_settings = process_settings(settings)
    start_end_json = load_settings(START_END_PATH)
    Generator = GameGenerator(merged_settings, start_end_json)
    return Generator

def main():
    DrawManager = GraphVisualizer(GRAPH_FILE_PATH)
    game_manager = GameManager(DrawManager)
    game_manager.InitGenerator()
    game_manager.InitPlayers()
    game_manager.InitRoadblocks()
    game_manager.InitCongestions()

    # Profile the main loop
    profiler = cProfile.Profile()
    profiler.enable()

    playing = True
    while playing:
        playing = game_manager.update()
        pygame.display.flip()
        clock.tick(60)

    profiler.disable()
    profiler.print_stats(sort='cumulative')

    pygame.quit()
    sys.exit()


# Run the simulation
if __name__ == "__main__":
    main()