import json
import pygame
import networkx as nx
import math
import uuid
from datetime import datetime
from roadblock import Roadblock
from ReportManager import ReportManager

# Constants
NODE_SIZE = 12
LINE_THICKNESS = 2
NODE_COLOR = (255, 255, 255)
EDGE_DEFAULT_COLOR = (0, 0, 0) 
PADDING = 20  # Padding for the map area

PLAYER_IMAGE_DEFAULT_PATH = 'src/imgs/navigation_red.png'
PLAYER_IMAGE_FAILED_PATH = 'src/imgs/navigation_gray.png'
PLAYER_IMAGE_DEVIATE_PATH = 'src/imgs/navigation_deviates.png'
PLAYER_IMAGE_DONE_PATH = 'src/imgs/navigation_green.png'
ROADBLOCK_REAL_IMAGE_PATH = 'src/imgs/roadblock_base.png'
ROADBLOCK_FAKE_IMAGE_PATH = 'src/imgs/roadblock_fake_reported.png'
ROADBLOCK_FAKE_SELECTED_PLAYER_IMAGE_PATH = 'src/imgs/roadblock_fake_reported_following.png'
ROADBLOCK_REPORTED_IMAGE_PATH = 'src/imgs/roadblock_reported.png'
ROADBLOCK_IMAGE_SIZE = 35
PLAYER_IMAGE_SIZE = 35

def congestion_color(congestion):
    """
    Returns a color based on congestion level.
    congestion = 1.0 -> black (no congestion)
    congestion = 0.75 -> yellow
    congestion = 0.5 -> orange
    congestion = 0.25 -> red (high congestion)
    """
    congestion = max(0.1, min(congestion, 1.0))

    if congestion >= 0.75:
        # Interpolate between Black (0,0,0) and Yellow (255,255,0)
        t = (congestion - 0.75) / (1.0 - 0.75)
        r = int(255 * (1 - t))  # from 255 (yellow) to 0 (black)
        g = int(255 * (1 - t))  # from 255 (yellow) to 0 (black)
        b = 0
        return (r, g, b)

    elif congestion >= 0.5:
        # Interpolate between Yellow (255,255,0) and Orange (255,165,0)
        t = (congestion - 0.5) / (0.75 - 0.5)
        r = 255
        g = int(165 + (255 - 165) * t)  # from 165 to 255
        b = 0
        return (r, g, b)

    elif congestion >= 0.25:
        # Interpolate between Orange (255,165,0) and Red (255,0,0)
        t = (congestion - 0.25) / (0.5 - 0.25)
        r = 255
        g = int(0 + (165 - 0) * (1 - t))  # from 165 to 0
        b = 0
        return (r, g, b)

    else:
        # Below 0.25 -> just red
        return (255, 0, 0)


class GraphVisualizer:
    def __init__(self, file_path, RM : ReportManager):
        self.G = None
        self.pos = None
        self.load_graph(file_path)
        self.font = pygame.font.SysFont('Tahoma', 14, bold=True)
        self.none_font = pygame.font.Font(None, 24)
        self.roadblocks = []
        self.reported_roadblocks = set()
        self.player_rects = []
        self.num_players_on_edge = {}
        self.roadblock_map = {}
        self.fake_roadblock_map = {}
        
        self.congestion_weights = {}

        self.enable_color_congestion = False
        self.RM = RM

        self.images = {
            'roadblock_real': pygame.image.load(ROADBLOCK_REAL_IMAGE_PATH).convert_alpha(),
            'roadblock_reported': pygame.image.load(ROADBLOCK_REPORTED_IMAGE_PATH).convert_alpha(),
            'roadblock_fake': pygame.image.load(ROADBLOCK_FAKE_IMAGE_PATH).convert_alpha(),
            'roadblock_fake_selected': pygame.image.load(ROADBLOCK_FAKE_SELECTED_PLAYER_IMAGE_PATH).convert_alpha(),
            'p_default': pygame.image.load(PLAYER_IMAGE_DEFAULT_PATH).convert_alpha(),
            'p_done': pygame.image.load(PLAYER_IMAGE_DONE_PATH).convert_alpha(),
            'p_deviate': pygame.image.load(PLAYER_IMAGE_DEVIATE_PATH).convert_alpha(),
            'p_failed': pygame.image.load(PLAYER_IMAGE_FAILED_PATH).convert_alpha()
        }

        self.images['roadblock_real'] = pygame.transform.scale(self.images['roadblock_real'], (ROADBLOCK_IMAGE_SIZE, ROADBLOCK_IMAGE_SIZE))
        self.images['roadblock_reported'] = pygame.transform.scale(self.images['roadblock_reported'], (ROADBLOCK_IMAGE_SIZE, ROADBLOCK_IMAGE_SIZE))
        self.images['roadblock_fake'] = pygame.transform.scale(self.images['roadblock_fake'], (ROADBLOCK_IMAGE_SIZE, ROADBLOCK_IMAGE_SIZE))
        self.images['roadblock_fake_selected'] = pygame.transform.scale(self.images['roadblock_fake_selected'], (ROADBLOCK_IMAGE_SIZE, ROADBLOCK_IMAGE_SIZE))
        self.images['p_default'] = pygame.transform.scale(self.images['p_default'], (PLAYER_IMAGE_SIZE, PLAYER_IMAGE_SIZE))
        self.images['p_done'] = pygame.transform.scale(self.images['p_done'], (PLAYER_IMAGE_SIZE, PLAYER_IMAGE_SIZE))
        self.images['p_deviate'] = pygame.transform.scale(self.images['p_deviate'], (PLAYER_IMAGE_SIZE, PLAYER_IMAGE_SIZE))
        self.images['p_failed'] = pygame.transform.scale(self.images['p_failed'], (PLAYER_IMAGE_SIZE, PLAYER_IMAGE_SIZE))



        for key in ['p_default', 'p_done', 'p_deviate', 'p_failed']:
            transparency = pygame.Surface(self.images[key].get_size(), pygame.SRCALPHA)
            transparency.fill((255, 255, 255, 200))  # 200 out of 255 for some transparency
            self.images[key].blit(transparency, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def load_graph(self, file_path):
        """Load the graph from a JSON file."""
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
            exit()
        except json.JSONDecodeError:
            print("Error: Invalid JSON format.")
            exit()

        self.G = nx.Graph()

        # Add nodes to the graph
        for i, node in enumerate(data['nodes']):
            rotated_x = node['y']
            rotated_y = -node['x']
            self.G.add_node(i, pos=(rotated_x, rotated_y))

        # Add edges between nodes
        for conn in data['connections']:
            node1 = conn['nodeIndex1']
            node2 = conn['nodeIndex2']
            
            x1, y1 = self.G.nodes[node1]['pos']
            x2, y2 = self.G.nodes[node2]['pos']

            # Euclid Distance
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            
            self.G.add_edge(node1, node2, weight=distance)

        # Get node positions
        self.pos = nx.get_node_attributes(self.G, 'pos')

    def get_pos(self, node_id):
        """Get the position of a node. Returns a tuple"""
        return self.pos.get(node_id)
    
    def get_graph(self):
        """Get the entire graph."""
        return self.G
    
    def get_connection_midpoint(self, node_a, node_b):
        """Gets the position two nodes and return the midpoint distance."""
        pos_a = self.get_pos(node_a)
        pos_b = self.get_pos(node_b)

        mid_x = (pos_a[0] + pos_b[0]) / 2
        mid_y = (pos_a[1] + pos_b[1]) / 2
        return (mid_x, mid_y)
    
    def get_neighbors(self, node_id):
        """Returns a list of neighboring nodes for the given node."""
        return list(self.G.neighbors(node_id))

    def is_valid_connection(self, node_a, node_b):
        """ Check if there is a connection between two nodes"""
        return self.G.has_edge(node_a, node_b)
    
    def InitRoadblockMap(self, mp):
        """ Called Once during setup. Maps pair of nodes to bool value if exists"""
        self.roadblock_map = mp
        self.fake_roadblock_map = {}
    
    def InitRoadblocks(self, roadblock: list):
        self.roadblocks = roadblock # creates reference to roadblocks list
        self.reported_roadblocks = set()

    def HasRoadblock(self, node_a, node_b, mp=None) -> tuple[Roadblock | None, bool]:
        """Check if there is a roadblock between two nodes (bidirectional) inside of provided map"""
        if mp is None:
            mp = self.roadblock_map
        roadblock = mp.get((node_a, node_b)) or mp.get((node_b, node_a))
        return (roadblock, roadblock is not None)

    def ReportRoadblock(self, id: int, node_a, node_b):
        """ Called when a player or AI requests report a roadblock to others"""
        roadblock, exists = self.HasRoadblock(node_a, node_b, self.roadblock_map)

        if not exists:
            roadblock, exists = self.HasRoadblock(node_a, node_b, self.fake_roadblock_map)
            if not exists:
                roadblock = Roadblock(node_a, node_b, self, False)
                self.fake_roadblock_map[(node_a, node_b)] = roadblock
                self.roadblocks.append(roadblock)

        roadblock.reported = True
        roadblock.times_reported += 1
        self.RM.add_to_report_history(id, roadblock.id, datetime.now().strftime('%H:%M:%S.%f')[:-3], roadblock.real, node_a, node_b)
        self.reported_roadblocks.add((node_a, node_b))
        
    def EnableColorCongestion(self, enable):
        """ Enable or Disable Color Congestion"""
        self.enable_color_congestion = enable

    def InitCongestionMap(self, mp):
        """ Called Once during setup. Maps pair of nodes to bool value if exists"""
        self.congestion_map = {}
        self.congestion_map = mp

    def InitCongestionWeightMap(self, mp):
        self.congestion_weights = {}
        self.congestion_weights = mp

    def InitPlayerCongestionMap(self, mp):
        self.player_congestion = {}
        self.player_congestion = mp
    
    def GetCongestion(self, node_a, node_b) -> float:
        """Returns the congestion factor (0-1) if congestion exists, otherwise returns 1 (no slowdown).
            If PlayerCongestion exists, this takes higher priority and return that congestion factor instead."""
        if self.congestion_map:
            road_congestion_factor = self.congestion_map.get((node_a, node_b), self.congestion_map.get((node_b, node_a), 1.0))
            if self.player_congestion is None:
                return road_congestion_factor
            # get the number of players on node_a, node_b edge
            num_players = self.num_players_on_edge.get((node_a, node_b), self.num_players_on_edge.get((node_b, node_a), 0))
            # if there is no value, return road_congestion_factor
            # if there is a value, multiply with the road_congestion_factor       
            return self.player_congestion.get(num_players, 1.0) * road_congestion_factor
            
        return 1.0
    
    def ChangePlayerEdgeLocation(self, edge = None , prev_edge = None):
        # Remove the player from the previous edge
        if prev_edge is not None:
            prev_node_a, prev_node_b = prev_edge
            prev_edge_a_b = (prev_node_a, prev_node_b)
            prev_edge_b_a = (prev_node_b, prev_node_a)
            if self.num_players_on_edge.get(prev_edge_a_b, 0) > 0:
                self.num_players_on_edge[prev_edge_a_b] -= 1
            elif self.num_players_on_edge.get(prev_edge_b_a, 0) > 0:
                self.num_players_on_edge[prev_edge_b_a] -= 1
            else:
                print(f"Error: Attempted to remove from an edge with zero players! ({prev_node_a}, {prev_node_b})")
                exit(1)
        # Add the player to the current edge
        # if the edge is (b, a) and exists, increment that, otherwise increment (a, b)
        if edge is not None:
            node_a, node_b = edge
            edge_a_b = (node_a, node_b)
            edge_b_a = (node_b, node_a)

            if edge_b_a in self.num_players_on_edge:
                self.num_players_on_edge[edge_b_a] += 1
            else:
                self.num_players_on_edge[edge_a_b] = self.num_players_on_edge.get(edge_a_b, 0) + 1

    
    def GetCongestionMultiplier(self, congestion_factor):
        """Given a congestion factor (0-1), return the distance multipler."""
        for (low, high), multiplier in self.congestion_weights.items():
            if low <= congestion_factor < high:
                return multiplier
        return 1 # There was no multiplier found


    def transform_position(self, x, y, scale, offset_x, offset_y, min_x, min_y):
        """Transforms the position based on scaling and offset."""
        return (
            int((x - min_x) * scale + offset_x),
            int((y - min_y) * scale + offset_y)
        )

    def calculate_scaling_and_offset(self, map_rect):
        """Calculate the scaling and offset values for drawing map."""
        min_x = min(self.pos[node][0] for node in self.pos)
        max_x = max(self.pos[node][0] for node in self.pos)
        min_y = min(self.pos[node][1] for node in self.pos)
        max_y = max(self.pos[node][1] for node in self.pos)

        scale_x = (map_rect.width - PADDING) / (max_x - min_x)
        scale_y = (map_rect.height - PADDING) / (max_y - min_y)
        scale = min(scale_x, scale_y)

        offset_x = (map_rect.width - (max_x - min_x) * scale) / 2 + map_rect.x
        offset_y = (map_rect.height - (max_y - min_y) * scale) / 2 + map_rect.y

        return scale, offset_x, offset_y, min_x, min_y

    def draw_graph(self, screen, map_rect):
        """Draw the graph on the given Pygame screen.
        If congestion is enabled, change the road color to orange
        """
        scale, offset_x, offset_y, min_x, min_y = self.calculate_scaling_and_offset(map_rect)

        for node1, node2 in self.G.edges():
            x1, y1 = self.transform_position(*self.pos[node1], scale, offset_x, offset_y, min_x, min_y)
            x2, y2 = self.transform_position(*self.pos[node2], scale, offset_x, offset_y, min_x, min_y)
            edge_color = EDGE_DEFAULT_COLOR
            if self.enable_color_congestion:
                congestion_value = self.GetCongestion(node1, node2)
                edge_color = congestion_color(congestion_value)
            pygame.draw.line(screen, edge_color, (x1, y1), (x2, y2), LINE_THICKNESS)

        for node in self.G.nodes():
            x, y = self.transform_position(*self.pos[node], scale, offset_x, offset_y, min_x, min_y)
            pygame.draw.circle(screen, NODE_COLOR, (x, y), NODE_SIZE)
            label = self.font.render(str(node), True, (0, 0, 0))
            screen.blit(label, label.get_rect(center=(x, y)))

    def draw_players(self, screen, players, map_rect):
        """Draw the players on the Pygame screen."""
        scale, offset_x, offset_y, min_x, min_y = self.calculate_scaling_and_offset(map_rect)
        self.player_rects = []
        for player in players:
            pos = player.pos
            if pos:
                x, y = self.transform_position(pos[0], pos[1], scale, offset_x, offset_y, min_x, min_y)
                
                if hasattr(player, 'finished') and player.finished:
                    player_image = self.images['p_done']
                elif hasattr(player, 'failed') and player.failed:
                    player_image = self.images['p_failed']
                elif player.deviates:
                    player_image = self.images['p_deviate']
                else:
                    player_image = self.images['p_default']

                # Rotate the image for each player (if needed)
                rotated_image = pygame.transform.rotate(player_image, player.direction)

                # Get the rect for the rotated image and set its position
                rotated_rect = rotated_image.get_rect(center=(x, y))

                self.player_rects.append((rotated_rect, player))

                # Draw the rotated image at the player's position
                screen.blit(rotated_image, rotated_rect)

    def draw_player_path(self, screen, selected_player, map_rect):
        """Draw the player's path as a light blue line on the screen. If they are deviated, purple line."""
        if not hasattr(self, 'path_surface'):
            # Create a surface for the path if it doesn't exist
            self.path_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            self.last_path = None  # Track the last path drawn

        path = selected_player.path  # List of nodes forming the path
        deviating = selected_player.deviates

        # Only redraw if the path or deviation status has changed
        if path != self.last_path or deviating != self.last_deviating:
            self.last_path = path
            self.last_deviating = deviating

            line_color = (173, 216, 230, 128)  # Light blue with alpha
            if deviating:
                line_color = (147, 112, 219, 128)  # Purple with alpha

            if len(path) < 2:
                return  # No need to draw if there are less than two nodes

            # Clear the path surface
            self.path_surface.fill((0, 0, 0, 0))  # Fill with transparent color

            scale, offset_x, offset_y, min_x, min_y = self.calculate_scaling_and_offset(map_rect)

            for i in range(len(path) - 1):
                x1, y1 = self.transform_position(*self.pos[path[i]], scale, offset_x, offset_y, min_x, min_y)
                x2, y2 = self.transform_position(*self.pos[path[i + 1]], scale, offset_x, offset_y, min_x, min_y)

                pygame.draw.line(self.path_surface, line_color, (x1, y1), (x2, y2), 5)

        screen.blit(self.path_surface, (0, 0))       
         
    def draw_roadblocks(self, screen, roadblocks: list[Roadblock], map_rect, selected_player=None):
        """Draw the roadblocks on the Pygame screen. If selected_player exists, any reported roadblocks will turn purple."""
        scale, offset_x, offset_y, min_x, min_y = self.calculate_scaling_and_offset(map_rect)

        for roadblock in roadblocks:
            pos = roadblock.pos
            x, y = self.transform_position(pos[0], pos[1], scale, offset_x, offset_y, min_x, min_y)

            if roadblock.real:
                if roadblock.reported:
                    roadblock_img = self.images['roadblock_reported']
                else:
                    roadblock_img = self.images['roadblock_real']
            else:
                if selected_player is not None and (
                    (roadblock.node_a, roadblock.node_b) in selected_player.false_roadblocks or 
                    (roadblock.node_b, roadblock.node_a) in selected_player.false_roadblocks
                ):
                    roadblock_img = self.images['roadblock_fake_selected']
                else:
                    roadblock_img = self.images['roadblock_fake']

            roadblock_rect = roadblock_img.get_rect(center=(x, y))
            screen.blit(roadblock_img, roadblock_rect)

            # Display times_reported if it's greater than 1
            if roadblock.times_reported > 1:
                text_surface = self.none_font.render(str(roadblock.times_reported), True, (255, 255, 255))  # White color
                text_rect = text_surface.get_rect(center=(x + 8, y + 8))  # Adjust the position as needed
                screen.blit(text_surface, text_rect)