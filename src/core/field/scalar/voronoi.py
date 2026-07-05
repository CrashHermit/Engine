import heapq


def voronoi_msd(
    adjacency: list[list[int]],
    seeds: dict[int, int],
    edge_weights: dict[tuple[int, int], float],
) -> dict[int, int]:
    node_region: dict[int, int] = {}
    priority_queue: list[tuple[float, int, int]] = []

    for seed_node, region_id in seeds.items():
        node_region[seed_node] = region_id
        heapq.heappush(priority_queue, (0.0, region_id, seed_node))

    while priority_queue:
        accumulated_weight, region_id, current_node = heapq.heappop(priority_queue)

        for neighbor_node in adjacency[current_node]:
            if neighbor_node not in node_region:
                node_region[neighbor_node] = region_id

                weight = edge_weights[(current_node, neighbor_node)]

                heapq.heappush(
                    priority_queue,
                    (accumulated_weight + weight, region_id, neighbor_node),
                )

    return node_region
