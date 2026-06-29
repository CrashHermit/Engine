import numpy as np

from src.worldgen.noise import NoiseFn


def generate_graph_voronoi(
    tiles: dict[int, Tile],
    seeds: dict[int, int],
    cost_function: Callable[[Tile, Tile], float]
) -> dict[int, int]:
    region_map: dict[int, int] = {}

    pq = []

    for start_tile_id, region_id in seeds.items():
        region_map[start_tile_id] = region_id
        heapq.heappush(pq, (0.0, region_id, start_tile_id))

    while pq:
        current_cost, region_id, current_tile_id = heapq.heappop(pq)
        current_tile = tiles[current_tile_id]

        for neighbor_id in current_tile.neighbors:
            if neighbor_id not in region_map:
                region_map[neighbor_id] = region_id

                neighbor_tile = tiles[neighbor_id]
                step_cost = cost_function(current_tile, neighbor_tile)

                total_cost = current_cost + step_cost
                heapq.heappush(pq, (total_cost, region_id, neighbor_id))

        return region_map
