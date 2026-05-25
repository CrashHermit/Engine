import heapq
from collections import defaultdict

from map.config import RiverConfig
from map.grid import TileData, hex_neighbors

Pos = tuple[int, int]


def fill_depressions(
    tiles: list[TileData],
    elevations: dict[Pos, int],
    rows: int,
    cols: int,
    sea_level: int,
) -> dict[Pos, int]:
    """
    Raise inland depressions so every land tile has a path to the ocean.

    Uses Priority Flood: seed from all ocean tiles, propagate outward ensuring
    each tile's spill elevation is the minimum needed to drain to the ocean.
    """
    filled = dict(elevations)
    heap: list[tuple[int, int, int]] = []
    visited: set[Pos] = set()

    for tile in tiles:
        pos = (tile.row, tile.col)
        if filled[pos] < sea_level:
            heapq.heappush(heap, (filled[pos], tile.row, tile.col))
            visited.add(pos)

    while heap:
        spill, row, col = heapq.heappop(heap)
        for _, (nr, nc) in hex_neighbors(row, col, rows, cols).items():
            npos = (nr, nc)
            if npos in visited:
                continue
            visited.add(npos)
            new_elev = max(filled[npos], spill)
            filled[npos] = new_elev
            heapq.heappush(heap, (new_elev, nr, nc))

    return filled


def compute_flow(
    tiles: list[TileData],
    elevations: dict[Pos, int],
    rows: int,
    cols: int,
    sea_level: int,
) -> dict[Pos, Pos | None]:
    """
    For every land tile, return the neighbor it drains into.
    Runs depression filling first so most rivers reach the ocean.
    Equal-elevation ties are broken by position to prevent cycles.
    Ocean tiles and true local minima (lakes) return None.
    """
    filled = fill_depressions(tiles, elevations, rows, cols, sea_level)
    flow_to: dict[Pos, Pos | None] = {}

    for tile in tiles:
        pos = (tile.row, tile.col)
        if filled[pos] < sea_level:
            flow_to[pos] = None
            continue

        neighbors = hex_neighbors(tile.row, tile.col, rows, cols)
        key_self = (filled[pos], pos)

        # Only flow to a neighbor with a strictly smaller (elevation, position) key.
        # This guarantees a DAG: A→B implies key(B) < key(A), so B cannot also →A.
        candidates = [n for n in neighbors.values() if (filled[n], n) < key_self]
        flow_to[pos] = min(candidates, key=lambda p: (filled[p], p)) if candidates else None

    return flow_to


def compute_flux(
    tiles: list[TileData],
    flow_to: dict[Pos, Pos | None],
    config: RiverConfig,
) -> dict[Pos, int]:
    """
    Compute watershed flux: every land tile contributes 1 unit of rain and
    passes its accumulated flux downstream. The result on each tile is the
    total number of tiles draining through it (its upstream catchment area).
    Tiles below config.min_flux are too small to be rivers.
    """
    # Count upstream contributors (in-degree) for topological processing
    in_degree: dict[Pos, int] = defaultdict(int)
    for tile in tiles:
        pos = (tile.row, tile.col)
        downstream = flow_to.get(pos)
        if downstream is not None:
            in_degree[downstream] += 1

    flux: dict[Pos, int] = {(t.row, t.col): 1 for t in tiles}

    # Process from headwaters (no upstream) toward the ocean
    queue = [(t.row, t.col) for t in tiles if in_degree.get((t.row, t.col), 0) == 0]
    while queue:
        next_queue = []
        for pos in queue:
            downstream = flow_to[pos]
            if downstream is not None:
                flux[downstream] += flux[pos]
                in_degree[downstream] -= 1
                if in_degree[downstream] == 0:
                    next_queue.append(downstream)
        queue = next_queue

    return flux
