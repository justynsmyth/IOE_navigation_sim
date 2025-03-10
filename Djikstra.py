import heapq
from collections import deque
from GraphVisualizer import GraphVisualizer

def Djikstra(start_node: int, end_node: int, GV: GraphVisualizer, player_known_roadblocks: set = None, player_avoid_roads: set = None, includeReportedRoadblocks: bool = False) -> deque:
    reported_roadblocks = GV.reported_roadblocks
    distances = {node: float('inf') for node in GV.G.nodes()}
    distances[start_node] = 0
    previous_nodes = {node: None for node in GV.G.nodes()}
    priority_queue = [(0, start_node)]  # (distance, node)

    visited = set()

    # Precompute conditions to avoid redundant checks
    check_player_known_roadblocks = player_known_roadblocks is not None
    check_player_avoid_roads = player_avoid_roads is not None

    while priority_queue:
        # Get the node with the smallest tentative distance
        current_distance, current_node = heapq.heappop(priority_queue)

        # If we reach the destination node, break out of the loop
        if current_node == end_node:
            break

        if current_node in visited:
            continue
        
        visited.add(current_node)

        for neighbor in GV.G.neighbors(current_node):
            if neighbor in visited:                
                continue

            if check_player_known_roadblocks:
                if (current_node, neighbor) in player_known_roadblocks or (neighbor, current_node) in player_known_roadblocks:
                    continue

            if check_player_avoid_roads:
                if (current_node, neighbor) in player_avoid_roads or (neighbor, current_node) in player_avoid_roads:
                    continue

            if includeReportedRoadblocks:
                if (current_node, neighbor) in reported_roadblocks or (neighbor, current_node) in reported_roadblocks:
                    continue

            weight = GV.G[current_node][neighbor]['weight']
            
            # If there are players or a congestion weight on an edge, get the multipler
            congestion_factor = GV.GetCongestion(current_node, neighbor)
            weight_mult = GV.GetCongestionMultiplier(congestion_factor)

            # Adjust the weight by multiplying it with the distance multiplier
            adjusted_weight = weight * weight_mult

            # Calculate the new tentative distance
            new_distance = current_distance + adjusted_weight

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(priority_queue, (new_distance, neighbor))

    path = deque()
    current_node = end_node
    # reverses from end to start and stores inside path deque
    while current_node is not None:
        path.appendleft(current_node)  # Add to the left of the deque
        current_node = previous_nodes[current_node] # follow the previous_nodes chain back to the beginning

    return path