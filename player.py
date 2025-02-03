import random
import uuid
import json
from Djikstra import Djikstra
import math
import csv
from datetime import datetime
import os
from GameGenerator import GameGenerator
from GraphVisualizer import GraphVisualizer

class Player:
    def __init__(self, player_id, start_node, end_node, graph_visualizer : GraphVisualizer, gen : GameGenerator, speed, time):
        self.uuid = player_id
        self.start = start_node
        self.end = end_node
        self.GV = graph_visualizer # map_drawer.py
        self.Gen = gen
        self.directory_time = time
        # initialize position to start position
        self.pos = self.get_start_pos()
        self.t = 0 # used for interpolation
        self.direction = 0
        self.curr_node_id = start_node

        self.finished = False 
        self.dest_node = None
        self.speed = speed

        self.create_position_csv()

        self.RoadblockOnCurrentRoute = False
        self.check_distance = 2
        self.traveled_distance = 0
        self.known_roadblocks = set() # personal list of roadblocks known to the player (does not have to be reported)

        self.path = Djikstra(self.curr_node_id, self.end, self.GV, self.known_roadblocks)  # Precomputed path. Needs to be updated frequently

        self.indices = {
            "FollowNav": 0,
            "PlayerReportRoadblock": 0,
            "PlayerReportCorrectRoadblock": 0
        }


    
    def __repr__(self):
        return (f"Player(UUID: {self.uuid}, "
                f"Start: {self.start}, "
                f"End: {self.end}, "
                f"Pos: {self.pos})")
    
    def get_start_pos(self):
        """Get the start position from the GraphVisualizer."""
        return self.GV.get_pos(self.start)

    def get_end_pos(self):
        """Get the end position from the GraphVisualizer."""
        return self.GV.get_pos(self.end)
    
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
        pos_x, pos_y = self.pos

        with open(self.position_csv, mode='a', newline='') as file:
            writer = csv.writer(file)
            time = datetime.now().strftime('%H:%M:%S.%f')
            writer.writerow([self.uuid, time ,pos_x, pos_y])

    def create_position_csv(self):
        """Creates new log position"""
        self.directory_path = os.path.join('logs', self.directory_time)
        os.makedirs(self.directory_path, exist_ok=True)
        self.position_csv = os.path.join(self.directory_path, 'position.csv') 
        with open(self.position_csv, mode='w', newline='') as file:
            w = csv.writer(file)
            w.writerow(['Player', 'Time', 'posX', 'posY'])
    
    def player_finish(self):
        self.finished = True
    
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
        """Update the position and direction over time. Checks for Roadblock."""
        follow_nav = self.Gen.ArrPlayerFollowsNavigation[self.indices["FollowNav"]]
        report_roadblock = self.Gen.ArrPlayerReportsRoadblock[self.indices["PlayerReportRoadblock"]]
        correct_roadblock_report = self.Gen.ArrPlayerReportsCorrectRoadblock[self.indices["PlayerReportCorrectRoadblock"]]

        if self.dest_node is None or self.t >= 1:
            if self.RoadblockOnCurrentRoute: 
                # Recalculate route if destination is the current node
                self.path = Djikstra(self.curr_node_id, self.end, self.GV, self.known_roadblocks)
            
            # Decide if player should follow navigation or deviate
            # if follow_nav:
            if len(self.path) > 1:
                self.set_curr_node_id(self.path.pop(0))
                self.dest_node = self.path[0]
                self.set_pos(self.GV.get_pos(self.curr_node_id))  # Reset exact position
                self.t = 0
                self.RoadblockOnCurrentRoute = False
                self.traveled_distance = 0  # reset back to zero
            else:
                self.set_curr_node_id(self.path[0])
                self.player_finish()
                return
            # else:
            #     # Deviate: Find all neighboring nodes excluding the intended one
            #     print("CHOOSING TO DEVIATE")
            #     neighbors = set(self.GV.get_neighbors(self.curr_node_id))
            #     if self.dest_node in neighbors:
            #         neighbors.remove(self.dest_node)  # Avoid the intended path
            #     if neighbors:
            #         self.dest_node = random.choice(list(neighbors))  # Choose a random path
            #     else:
            #         self.dest_node = self.path[0]  # If no alternatives, stay on course
            # self.indices["FollowNav"] += 1


        orig_pos = self.GV.get_pos(self.curr_node_id) if not self.RoadblockOnCurrentRoute else self.roadblock_position
        dest_pos = self.GV.get_pos(self.dest_node)

        if orig_pos is None or dest_pos is None:
            raise ValueError("Node positions not found!")

        x2, y2 = orig_pos
        x1, y1 = dest_pos

        # Calculate distance between the current and destination node
        distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

        # calculate speed of player (if there are congestions)
        congestion_value = self.GV.GetCongestion(self.curr_node_id, self.dest_node)  # Range: 0.1 - 1.0
        adjusted_speed = self.speed * congestion_value  # Reduce speed based on congestion

        # Calculate delta_t based on desired speed
        if distance > 0:
            delta_t = min(adjusted_speed / max(distance, 1e-6), 1)
        else:
            delta_t = 1  # Edge case handling

        # Increment t (normalized progress)
        self.t = min(self.t + delta_t, 1)

        interpolated_x = x2 + self.t * (x1 - x2)
        interpolated_y = y2 + self.t * (y1 - y2)
        self.set_pos((interpolated_x, interpolated_y))

        # Track traveled distance
        self.traveled_distance += adjusted_speed * delta_t

        if self.traveled_distance >= self.check_distance:
            if self.GV.HasRoadblock(self.curr_node_id, self.dest_node):
                print(f"Roadblock detected between {self.curr_node_id} and {self.dest_node}. Returning to current node.")
                # Detour back to current node
                self.known_roadblocks.add((self.curr_node_id, self.dest_node))

                self.dest_node = self.curr_node_id  # Set destination to current node
                self.roadblock_position = self.get_pos()  # Store the roadblock position
                self.set_direction(self.calculate_direction(self.pos, orig_pos))
                self.RoadblockOnCurrentRoute = True
                self.t = 0
        else:
            self.set_direction(self.calculate_direction(orig_pos, dest_pos))

        
def LoadPlayerInfo(json_path, time, GV, Gen: GameGenerator):
    ''' Generates player array based on start_end_indices.json file.'''
    players = []
    with open(json_path, 'r') as file:
        data = json.load(file)
        for i, (start, end) in enumerate(data["start_end_indices"]):
            player_index = i
            speed = Gen.players_speeds[i]
            players.append(Player(player_index, start, end, GV, Gen, speed, time))
    return players