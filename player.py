import random
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
        self.id = player_id
        self.start = start_node
        self.end = end_node
        self.GV = graph_visualizer # map_drawer.py
        self.Gen = gen
        self.directory_time = time
        # initialize position to start position
        self.pos = self.get_start_pos()
        self.t = 0 # used for interpolation
        self.direction = 0

        self.finished = False 
        self.speed = speed

        self.create_position_csv()

        self.RoadblockOnPrevRoute = False
        self.CheckedRoadblockOnCurrentRoute = False
        self.ReportIfRoadblock = False
        self.check_distance = 2
        self.traveled_distance = 0
        self.known_roadblocks = set() # personal list of roadblocks known to the player (does not have to be reported)
        self.false_roadblocks = set() # personal list of roadblocks that were falsely reported by player

        self.curr_node_id = start_node 
        self.path = Djikstra(self.curr_node_id, self.end, self.GV) # Precomputed path. Needs to be updated frequently
        self.curr_node_id = start_node
        print(f"player {self.id} started at {start_node}")
        self.Gen.add_to_nav_history(self.id, datetime.now().strftime('%H:%M:%S.%f'), "Initial", self.curr_node_id, self.path.copy())
        self.dest_node = self.path[1]
        self.is_initial = True

        self.deviation_ticks = 0  # Number of update cycles to show deviation effect
        self.deviation_duration = 10  # Adjust this to control how long the effect lasts
        self.deviates = False



    def __repr__(self):
        return (f"Player(ID: {self.id}, "
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
        if not self.is_initial:
            if self.curr_node_id == node_id:
                print(f"player {self.id} has detoured back to {node_id}")
            else:
                print(f"player {self.id} has moved to {node_id}")
        self.curr_node_id = node_id

    def log_position(self):
        """Log the current position to a CSV file."""
        pos_x, pos_y = self.pos

        with open(self.position_csv, mode='a', newline='') as file:
            writer = csv.writer(file)
            time = datetime.now().strftime('%H:%M:%S.%f')
            writer.writerow([self.id, time ,pos_x, pos_y])

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
    
    def SetPlayerPath(self) -> bool:
        '''Returns whether the Player has finished or not'''
        if len(self.path) > 1:
            self.dest_node = self.path[1]
            self.set_pos(self.GV.get_pos(self.curr_node_id))  # Reset exact position
            self.t = 0
            self.RoadblockOnPrevRoute = False
            self.CheckedRoadblockOnCurrentRoute = False
            self.traveled_distance = 0  # reset back to zero
            return False
        else:
            assert(self.path[0] == self.end)
            self.player_finish() 
            return True
        
    def CheckPlayerFollowsNav(self):
        '''Checks if the player has decided to follow the navigation or not.'''
        follow_nav = self.Gen.GetNextFollowNavigation(self.id)
        if follow_nav:
            if not self.is_initial:
                self.Gen.add_to_nav_history(self.id, datetime.now().strftime('%H:%M:%S.%f'), "Waypoint Reached", self.curr_node_id, self.path.copy())
        else:
            print(f"Player {self.id} decides to deviate from navigation")
            # If a player is returning to their origin node (due to roadblock)
            # player will find its own path given its known roadblocks, the path it does not want to take, and will still traverse path that it knows are false roadblocks
            self.deviates = True
            self.deviation_ticks = self.deviation_duration 
            self.path = Djikstra(self.curr_node_id, self.end, self.GV, self.known_roadblocks, {(self.curr_node_id, self.path[1])}, self.false_roadblocks)
    
    def OnPlayerReturnsFromRoadblock(self):
        '''Function called when player returns from a roadblock.'''
        # If player reported roadblock, Djikstra will automatically find best path for player
        # Will try and avoid any paths reported already
        if self.ReportIfRoadblock:
            print(f"System finding new route for player {self.id} due to roadblock report")
            self.path = Djikstra(self.curr_node_id, self.end, self.GV, None, None, None, True)
            print(f"New path: {self.path}")
            self.Gen.add_to_nav_history(self.id, datetime.now().strftime('%H:%M:%S.%f'), "Detour", self.curr_node_id, self.path.copy()) 
        else:
            # Player did not report. Player will need to find next best path given its own knowledge.
            self.path = Djikstra(self.curr_node_id, self.end, self.GV, self.known_roadblocks, None, self.false_roadblocks)
        
    def checkForDeviationTimer(self):
        if self.deviation_ticks > 0:
            self.deviation_ticks -= 1
            self.deviates = True
        else:
            self.deviates = False

    def update(self):
        """Update the position and direction over time. Checks for Roadblock."""
        # Has player reached a dest_node by their .t value exceededing the normalized progress (1 is max)
        # If initial, still need to check if the player will deviate or not
        self.checkForDeviationTimer()
        if self.t >= 1:
            self.path.pop(0) # delete prev node from current pathi=
            if len(self.path) > 1:
                self.set_curr_node_id(self.dest_node)
                if self.RoadblockOnPrevRoute:
                    self.OnPlayerReturnsFromRoadblock()
                self.CheckPlayerFollowsNav()
            if self.SetPlayerPath():
                return
        elif self.is_initial:
            self.CheckPlayerFollowsNav()
            self.set_curr_node_id(self.path[0])
            if self.SetPlayerPath():
                return
            self.is_initial = False

        # Mark location of where player started from (node or roadblock)
        orig_pos = self.GV.get_pos(self.curr_node_id) if not self.RoadblockOnPrevRoute else self.roadblock_position
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
            _, exists = self.GV.HasRoadblock(self.curr_node_id, self.dest_node)
            if exists and not self.RoadblockOnPrevRoute:
                print(f"Roadblock detected between {self.curr_node_id} and {self.dest_node}. Returning to current node.")
                # Detour back to current node
                self.known_roadblocks.add((self.curr_node_id, self.dest_node))

                self.ReportIfRoadblock = self.Gen.GetNextReportsRoadblockIfRoadblock(self.id)
                if self.ReportIfRoadblock:
                    self.GV.ReportRoadblock(self.curr_node_id, self.dest_node)
                    print(f"Player {self.id} reported roadblock between {self.curr_node_id} and {self.dest_node}")

                self.dest_node = self.curr_node_id  # Set destination to current node
                self.roadblock_position = self.get_pos()  # Store the roadblock position
                self.set_direction(self.calculate_direction(self.pos, orig_pos))
                self.RoadblockOnPrevRoute = True
                self.CheckedRoadblockOnCurrentRoute = True
                self.t = 0
            elif not self.CheckedRoadblockOnCurrentRoute:
                ReportRoadblockIfNoRoadblock = self.Gen.GetNextReportsRoadblockIfNoRoadblock(self.id)
                if ReportRoadblockIfNoRoadblock:
                    self.GV.ReportRoadblock(self.curr_node_id, self.dest_node)
                    print(f"Player {self.id} false reported a roadblock between {self.curr_node_id} and {self.dest_node}")
                    self.false_roadblocks.add((self.curr_node_id, self.dest_node))
                self.CheckedRoadblockOnCurrentRoute = True
        else:
            self.set_direction(self.calculate_direction(orig_pos, dest_pos))

def LoadPlayerInfo(json_path, time, GV, Gen: GameGenerator) -> list[Player]:
    ''' Generates player array based on start_end_indices.json file.'''
    players = []
    with open(json_path, 'r') as file:
        data = json.load(file)
        for i, (start, end) in enumerate(data["start_end_indices"]):
            player_index = i
            speed = Gen.players_speeds[i]
            players.append(Player(player_index, start, end, GV, Gen, speed, time))
    return players