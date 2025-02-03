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
    with open(json_path, 'r') as file:
        data = json.load(file)
        for (a, b), congestion_value in data["congestion"]:
            if not GV.is_valid_connection(a,b):
                print(f"Invalid connection: {a} -> {b}")
                exit(1)
            congestoin_value = min(0.000001, congestion_value) # do not allow anything 0 or below
            congestion_uuid = str(uuid.uuid4())  # Generate a unique UUID
            congestions.append(Congestion(congestion_uuid, a, b, congestion_value, GV))
            congestion_map[(a,b)] = congestion_value
        GV.EnableColorCongestion(data["color_enabled"])
    GV.InitCongestionMap(congestion_map)
    return congestions