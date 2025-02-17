import heapq
from GraphVisualizer import GraphVisualizer


def Djikstra(start_node: int, end_node: int, GV: GraphVisualizer, player_known_roadblocks: set = None, player_avoid_roads: set = None, player_false_roadblocks: set = None, includeReportedRoadblocks: bool = False):
    reported_roadblocks = GV.reported_roadblocks
    distances = {node: float('inf') for node in GV.G.nodes()}
    distances[start_node] = 0
    previous_nodes = {node: None for node in GV.G.nodes()}
    priority_queue = [(0, start_node)]  # (distance, node)

    visited = set()
    while priority_queue:
        # Get the node with the smallest tentative distance
        current_distance, current_node = heapq.heappop(priority_queue)

        # If we reach the destination node, break out of the loop
        if current_node == end_node:
            break

        if current_node in visited:
            continue
        
        visited.add(current_node)

        # Check all neighbors (connected nodes) of the current node
        for neighbor in GV.G.neighbors(current_node):
            if neighbor in visited:                
                continue

            # Skip the roadblocks in player_known_roadblocks
            if player_known_roadblocks is not None:
                if (current_node, neighbor) in player_known_roadblocks or (neighbor, current_node) in player_known_roadblocks:
                    # print("Player knows about this roadblock. Avoiding this path")
                    continue

            if player_avoid_roads is not None:
                if (current_node, neighbor) in player_avoid_roads or (neighbor, current_node) in player_avoid_roads:
                    # print("Player purposefully avoiding this road")
                    continue

            # If player_false_roadblocks provided, need to avoid reports reported by others
            # Exception: if a player knows they false reported that roadblock (player_false_roadblocks), they will traverse that path  
            if player_false_roadblocks is not None:
                if (current_node, neighbor) in reported_roadblocks and (current_node, neighbor) not in player_false_roadblocks:
                    continue
                if (neighbor, current_node) in reported_roadblocks and (neighbor, current_node) not in player_false_roadblocks:
                    continue
            
            if includeReportedRoadblocks:
                if (current_node, neighbor) in reported_roadblocks or (neighbor, current_node) in reported_roadblocks:
                    # print("System knows that players know this roadblock exists and will avoid this path")
                    continue

            weight = GV.G[current_node][neighbor]['weight']

            new_distance = current_distance + weight

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(priority_queue, (new_distance, neighbor))

    # Reconstruct the path from end_node to start_node
    path = []
    current_node = end_node
    while current_node is not None:
        path.append(current_node)
        current_node = previous_nodes[current_node]

    path.reverse()

    return path