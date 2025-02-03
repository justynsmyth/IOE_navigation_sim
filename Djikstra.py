import heapq

def Djikstra(start_node, end_node, GV, player_known_roadblocks):
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
            if (current_node, neighbor) in player_known_roadblocks or (neighbor, current_node) in player_known_roadblocks:
                print(f"Rerouting around roadblock")
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