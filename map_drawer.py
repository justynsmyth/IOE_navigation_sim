import json
import pygame
import networkx as nx
import math

# Constants
NODE_SIZE = 12
LINE_THICKNESS = 2
NODE_COLOR = (255, 255, 255)
EDGE_COLOR = (0, 0, 0) 
PADDING = 20  # Padding for the map area

PLAYER_IMAGE_PATH = 'src/imgs/navigation_red.png'
PLAYER_IMAGE_SIZE = 35


class GraphVisualizer:
    def __init__(self, file_path):
        self.G = None
        self.pos = None
        self.load_graph(file_path)

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
        """Draw the graph on the given Pygame screen."""
        scale, offset_x, offset_y, min_x, min_y = self.calculate_scaling_and_offset(map_rect)

        for edge in self.G.edges():
            node1, node2 = edge
            x1, y1 = self.transform_position(*self.pos[node1], scale, offset_x, offset_y, min_x, min_y)
            x2, y2 = self.transform_position(*self.pos[node2], scale, offset_x, offset_y, min_x, min_y)
            pygame.draw.line(screen, EDGE_COLOR, (x1, y1), (x2, y2), LINE_THICKNESS)

        for node in self.G.nodes():
            x, y = self.transform_position(*self.pos[node], scale, offset_x, offset_y, min_x, min_y)
            pygame.draw.circle(screen, NODE_COLOR, (x, y), NODE_SIZE)
            label = pygame.font.SysFont('Tahoma', 14, bold=True).render(str(node), True, (0, 0, 0))
            label_rect = label.get_rect(center=(x, y))
            screen.blit(label, label_rect)

    def draw_players(self, screen, players, map_rect):
        """Draw the players on the Pygame screen."""
        scale, offset_x, offset_y, min_x, min_y = self.calculate_scaling_and_offset(map_rect)

        for player in players:
            pos = player.pos
            if pos:
                x, y = self.transform_position(pos[0], pos[1], scale, offset_x, offset_y, min_x, min_y)
                
                # Load the player image and scale it
                player_image = pygame.image.load(PLAYER_IMAGE_PATH).convert_alpha()
                player_image = pygame.transform.scale(player_image, (PLAYER_IMAGE_SIZE, PLAYER_IMAGE_SIZE))
                
                # Rotate the image for each player (if needed)
                rotated_image = pygame.transform.rotate(player_image, player.direction)
                
                # Get the rect for the rotated image and set its position
                rotated_rect = rotated_image.get_rect(center=(x, y))

                # Draw the rotated image at the player's position
                screen.blit(rotated_image, rotated_rect)
