import json
import pygame
import networkx as nx
import math

# Constants
NODE_SIZE = 12
LINE_THICKNESS = 2
NODE_COLOR = (255, 255, 255)
EDGE_DEFAULT_COLOR = (0, 0, 0) 
PADDING = 20  # Padding for the map area

PLAYER_IMAGE_DEFAULT_PATH = 'src/imgs/navigation_red.png'
PLAYER_IMAGE_DONE_PATH = 'src/imgs/navigation_green.png'
ROADBLOCK_IMAGE_PATH ='src/imgs/roadblock_base.png'
ROADBLOCK_IMAGE_SIZE = 50
PLAYER_IMAGE_SIZE = 35

def congestion_color(congestion):
    """
    Returns a color based on congestion level.
    congestion = 1.0 -> black (no congestion)
    congestion = 0.75 -> yellow
    congestion = 0.5 -> orange
    congestion = 0.25 -> red (high congestion)
    """
    # Ensure valid range (0.1 to 1.0)
    congestion = max(0.1, min(congestion, 1.0))

    if congestion >= 0.75:
        # Interpolate between black (0,0,0) and yellow (255,255,0)
        ratio = (1.0 - congestion) * 4
        r = int(255 * ratio)
        g = int(255 * ratio)
        return (r, g, 0)
    elif congestion >= 0.5:
        # Interpolate between yellow (255,255,0) and orange (255,165,0)
        ratio = (0.75 - congestion) * 4
        g = int(255 - 90 * ratio)
        return (255, max(0, g), 0)
    else:
        # Interpolate between orange (255,165,0) and red (255,0,0)
        ratio = (0.5 - congestion) * 4
        g = int(165 * (1 - ratio))
        return (255, max(0, g), 0)

class GraphVisualizer:
    def __init__(self, file_path):
        self.G = None
        self.pos = None
        self.load_graph(file_path)
        self.font = pygame.font.SysFont('Tahoma', 14, bold=True)


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

    def HasRoadblock(self, node_a, node_b) -> bool:
        """ Check if there is a roadblock between two nodes. Checks both directoins since connections are bidirectional"""
        return self.roadblock_map.get((node_a, node_b)) or self.roadblock_map.get((node_b, node_a), False)
    
    def EnableColorCongestion(self, enable):
        """ Enable or Disable Color Congestion"""
        self.enable_color_congestion = enable

    def InitCongestionMap(self, mp):
        """ Called Once during setup. Maps pair of nodes to bool value if exists"""
        self.congestion_map = mp
    
    def GetCongestion(self, node_a, node_b) -> float:
        """Returns the congestion factor (0-1) if congestion exists, otherwise returns 1 (no slowdown)."""
        return self.congestion_map.get((node_a, node_b), self.congestion_map.get((node_b, node_a), 1.0))

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

        for player in players:
            pos = player.pos
            if pos:
                x, y = self.transform_position(pos[0], pos[1], scale, offset_x, offset_y, min_x, min_y)
                
                # Load the player image and scale it
                player_image = pygame.image.load(PLAYER_IMAGE_DEFAULT_PATH).convert_alpha()
                if hasattr(player, 'finished') and player.finished:
                    player_image = pygame.image.load(PLAYER_IMAGE_DONE_PATH).convert_alpha()
 
                player_image = pygame.transform.scale(player_image, (PLAYER_IMAGE_SIZE, PLAYER_IMAGE_SIZE))

                # Make the player image slightly transparent
                transparency = pygame.Surface(player_image.get_size(), pygame.SRCALPHA)
                transparency.fill((255, 255, 255, 200))  # 200 out of 255 for some transparency
                player_image.blit(transparency, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                # Rotate the image for each player (if needed)
                rotated_image = pygame.transform.rotate(player_image, player.direction)
                
                # Get the rect for the rotated image and set its position
                rotated_rect = rotated_image.get_rect(center=(x, y))

                # Draw the rotated image at the player's position
                screen.blit(rotated_image, rotated_rect)

    def draw_roadblocks(self, screen, roadblocks, map_rect):
        """Draw the roadblocks on the Pygame screen."""
        scale, offset_x, offset_y, min_x, min_y = self.calculate_scaling_and_offset(map_rect)

        for roadblock in roadblocks:
            pos = roadblock.pos
            if pos:
                x, y = self.transform_position(pos[0], pos[1], scale, offset_x, offset_y, min_x, min_y)

                roadblock_img = pygame.image.load(ROADBLOCK_IMAGE_PATH).convert_alpha()
                roadblock_img = pygame.transform.scale(roadblock_img, (ROADBLOCK_IMAGE_SIZE, ROADBLOCK_IMAGE_SIZE))
                roadblock_rect = roadblock_img.get_rect(center=(x, y))
                screen.blit(roadblock_img, roadblock_rect)