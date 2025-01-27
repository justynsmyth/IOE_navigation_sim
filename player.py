import uuid
import json
from Djikstra import Djikstra
import math
import csv
from datetime import datetime
import os

class Player:
    def __init__(self, player_id, start_node, end_node, graph_visualizer, speed):
        self.uuid = player_id
        self.start = start_node
        self.end = end_node
        self.graph_visualizer = graph_visualizer # map_drawer.py
        # initialize position to start position
        self.pos = self.get_start_pos()
        self.t = 0 # used for interpolation
        self.direction = 0
        self.curr_node_id = start_node
        self.path = Djikstra(self.curr_node_id, self.end, self.graph_visualizer.G)  # Precomputed path. Needs to be updated frequently

        self.dest_node = None

        self.speed = speed

        self.create_position_csv()
    
    def __repr__(self):
        return (f"Player(UUID: {self.uuid}, "
                f"Start: {self.start}, "
                f"End: {self.end}, "
                f"Pos: {self.pos})")
    
    def get_start_pos(self):
        """Get the start position from the GraphVisualizer."""
        return self.graph_visualizer.get_pos(self.start)

    def get_end_pos(self):
        """Get the end position from the GraphVisualizer."""
        return self.graph_visualizer.get_pos(self.end)
    
    def get_pos(self):
        """Get the current position of the player."""
        return self.pos
    
    def get_direction(self):
        """Get the direction of the player."""
        return self.direction

    def get_curr_node_id(self):
        """Get the current node id of the player."""
        return self.curr_node_id
    
    def set_pos(self, pos):
        """Set the position of the player."""
        self.pos = pos
        self.log_position()
    
    def set_direction(self, direction):
        """Set the direction of the player."""
        self.direction = direction
    
    def set_curr_node_id(self, node_id):
        """Set the current node id of the player."""
        self.curr_node_id = node_id
        print(f"player has moved to {node_id}")

    def log_position(self):
        """Log the current position to a CSV file."""
        time_now = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Trim to ms
        pos_x, pos_y = self.pos

        with open(self.position_csv, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([self.uuid, time_now, pos_x, pos_y])

    def create_position_csv(self):
        """Creates new  log position"""
        time_now = datetime.now().strftime("%m%d_%H%M%S")
        self.directory_path = os.path.join('logs', time_now)
        os.makedirs(self.directory_path, exist_ok=True)
        self.position_csv = os.path.join(self.directory_path, 'position.csv') 

    
    def calculate_direction(self, curr_pos, dest_pos):
        """Calculate the direction angle from curr_pos to dest_pos."""
        x1, y1 = curr_pos
        x2, y2 = dest_pos

        angle_radians = math.atan2(y2 - y1, x2 - x1)
        angle_degrees = math.degrees(angle_radians)
        
        # adjust the angle to be positive
        rotation_angle = angle_degrees
        if rotation_angle < 0:
            rotation_angle += 360

        # Adjust so that the image's 0 degrees is upwards
        rotation_angle = (450 - rotation_angle) % 360
        
        return rotation_angle
    
    def update(self):
        """Update the position and direction over time."""
        if self.dest_node is None or self.t >= 1:
            if len(self.path) > 1:
                self.set_curr_node_id(self.path.pop(0))
                self.dest_node = self.path[0]
                self.set_pos(self.graph_visualizer.get_pos(self.curr_node_id))  # Reset exact position
                self.t = 0
            else:
                return

        curr_pos = self.graph_visualizer.get_pos(self.curr_node_id)
        dest_pos = self.graph_visualizer.get_pos(self.dest_node)

        if curr_pos is None or dest_pos is None:
            raise ValueError("Node positions not found!")

        x2, y2 = curr_pos
        x1, y1 = dest_pos

        # Calculate distance between the current and destination node
        distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

        # Calculate delta_t based on desired speed
        if distance > 0:
            delta_t = self.speed / distance
        else:
            delta_t = 1  # Edge case handling

        # Increment t (normalized progress)
        self.t = min(self.t + delta_t, 1)

        # Lerp
        interpolated_x = x2 + self.t * (x1 - x2)
        interpolated_y = y2 + self.t * (y1 - y2)
        self.set_pos((interpolated_x, interpolated_y))

        self.set_direction(self.calculate_direction(curr_pos, dest_pos))
        
def load_player_info(json_path, setup_path, GV):
    ''' Generates player array based on start_end_indices.json file.'''
    players = []
    with open(json_path, 'r') as file:
        with open(setup_path, 'r') as file2:
            data = json.load(file)
            setup = json.load(file2)
            for start, end in data["start_end_indices"]:
                player_uuid = str(uuid.uuid4())  # Generate a unique UUID
                players.append(Player(player_uuid, start, end, GV, setup["PlayerSpeed"]))
    return players