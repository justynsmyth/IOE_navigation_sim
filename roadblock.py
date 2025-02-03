import os
import json
import uuid

class Roadblock:
    def __init__(self, uuid, node_a, node_b, graph_visualizer):
        self.uuid = uuid
        self.graph_visualizer = graph_visualizer
        self.node_a = node_a
        self.node_b = node_b
        self.pos = self.graph_visualizer.get_connection_midpoint(node_a, node_b)
        self.reported = False

    def __repr__(self):
        return (f"Roadblock(UUID: {self.uuid}, "
                f"node_a: {self.node_a}, "
                f"node_b: {self.node_b}, "
                f"Pos: {self.pos})")

    def report(self):
        self.reported = True
        self.graph_visualizer.update_roadblock(self.roadblock_id, self.pos)

    def update(self):
        """Draw and update whether a roadblock has been reported."""
        pass

    def get_roadblock_id(self):
        return self.roadblock_id
    

def LoadRoadblockInfo(json_path, GV):
    ''' Generates roadblock array based on roadblock.json file.'''
    roadblocks = []
    roadblock_map = {}
    with open(json_path, 'r') as file:
        data = json.load(file)
        for a, b in data["roadblock"]:
            if not GV.is_valid_connection(a,b):
                print(f"Invalid connection: {a} -> {b}")
                exit(1)
            roadblock_uuid = str(uuid.uuid4())  # Generate a unique UUID
            roadblocks.append(Roadblock(roadblock_uuid, a, b, GV))
            roadblock_map[(a,b)] = True
    GV.InitRoadblockMap(roadblock_map)
    return roadblocks