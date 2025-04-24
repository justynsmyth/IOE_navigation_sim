import json

class Roadblock:
    _id_ctr = 0
    def __init__(self, node_a, node_b, graph_visualizer, real = False):
        self.id = Roadblock._id_ctr
        Roadblock._id_ctr += 1
        self.graph_visualizer = graph_visualizer
        self.node_a = node_a
        self.node_b = node_b
        self.pos = self.graph_visualizer.get_connection_midpoint(node_a, node_b)
        self.reported = False # whether this roadblock has been reported by a player
        self.real = real # whether or not this roadblock is real
        self.times_reported = 0 # number of people that reported on this roadblock

    def __repr__(self):
        return (f"Roadblock(UUID: {self.id}, "
                f"node_a: {self.node_a}, "
                f"node_b: {self.node_b}, "
                f"Pos: {self.pos})")

    def report(self):
        self.reported = True
        self.graph_visualizer.update_roadblock(self.roadblock_id, self.pos)


    def get_roadblock_id(self):
        return self.roadblock_id

    @staticmethod
    def reset_roadblock_ctr():
        Roadblock._id_ctr = 0
    

def LoadRoadblockInfo(json_path, GV) -> list[Roadblock]:
    ''' Generates roadblock array based on roadblock.json file.'''
    roadblocks = []
    roadblock_map = {}
    with open(json_path, 'r') as file:
        data = json.load(file)
        for a, b in data["roadblock"]:
            if not GV.is_valid_connection(a,b):
                print(f"Invalid connection: {a} -> {b}")
                exit(1)
            roadblock = Roadblock(a, b, GV, True)
            roadblocks.append(roadblock)
            roadblock_map[(a, b)] = roadblock
    GV.InitRoadblockMap(roadblock_map)
    GV.InitRoadblocks(roadblocks)
    return roadblocks