import os
import json
import uuid

class Congestion:
    def __init__(self, uuid, node_a, node_b, congestion_val, graph_visualizer):
        self.uuid = uuid
        self.graph_visualizer = graph_visualizer
        self.node_a = node_a
        self.node_b = node_b
        self.congestion_value = congestion_val


    def __repr__(self):
        return (f"Congestion(UUID: {self.uuid}, "
                f"node_a: {self.node_a}, "
                f"node_b: {self.node_b}, "
                f"congestion_value: {self.congestion_value}")

def LoadCongestionInfo(json_path, GV):
    ''' Generates congestion array based on congestion.json file.'''
    congestions = []
    congestion_map = {}
    congestion_weights_map = {}
    player_congestion_map = {}
    with open(json_path, 'r') as file:
        data = json.load(file)
        for (a, b), congestion_value in data["congestion"]:
            if not GV.is_valid_connection(a,b) or (congestion_value <= 0) or (congestion_value > 1):
                print(f"Invalid connection: {a} -> {b}")
                exit(1)
            congestion_value = min(1, congestion_value) # do not allow anything higher than 1
            if congestion_value == 0:
                print(f"Invalid congestion value: {congestion_value}. Needs to be larger than 0!")
                exit(1)
            congestion_value = max(0.00001, congestion_value)
            congestion_uuid = str(uuid.uuid4())  # Generate a unique UUID
            congestions.append(Congestion(congestion_uuid, a, b, congestion_value, GV))
            congestion_map[(a,b)] = congestion_value
        for (a, b), congestion_weight in data["congestion_weights"]:
            if (a > b) or (a < 0):
                print(f"Invalid connection weight: (a, b].")
                exit(1)
            congestion_weights_map[(a,b)] = congestion_weight
        # player congestion is [inclusive, exclusive)
        for (a, b), player_congestion in data["player_congestion"]:
            if (a > b) or (a <= 0):
                print(f"Invalid connection: {a} -> {b}")
                exit(1)
            for i in range(a, b):
                player_congestion_map[i] = player_congestion
        GV.EnableColorCongestion(data["color_enabled"])
    GV.InitCongestionMap(congestion_map)
    GV.InitCongestionWeightMap(congestion_weights_map)
    GV.InitPlayerCongestionMap(player_congestion_map)
    return congestions