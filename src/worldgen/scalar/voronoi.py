import heapq
from collections.abc import Callable

def voronoi_msd(
    adjacency: list[list[int]],
    seeds: dict[int, int],
    cost_function: Callable[[int, int], float],
) -> dict[int, int]:
    region_map = {}
    pq = []

    for start_id, region_id in seeds.items():
        region_map[start_id] = region_id
        heapq.heappush(pq, (0.0, region_id, start_id))

    while pq:
        current_cost, region_id, current_id = heapq.heappop(pq)

        for neighbor_id in adjacency[current_id]:
            if neighbor_id not in region_map:
                region_map[neighbor_id] = region_id

                step_cost = cost_function(current_id, neighbor_id)

                heapq.heappush(pq, (current_cost + step_cost, region_id, neighbor_id))

    return region_map
