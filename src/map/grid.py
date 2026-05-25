from dataclasses import dataclass

# Neighbor offsets for offset-coordinate hex grids (even-r and odd-r rows differ).
# Directions: E, W, NE, NW, SE, SW — every tile has exactly these 6.
_EVEN_DELTAS: dict[str, tuple[int, int]] = {
    "E":  ( 0, +1),
    "W":  ( 0, -1),
    "NE": (-1, +1),
    "NW": (-1,  0),
    "SE": (+1, +1),
    "SW": (+1,  0),
}
_ODD_DELTAS: dict[str, tuple[int, int]] = {
    "E":  ( 0, +1),
    "W":  ( 0, -1),
    "NE": (-1,  0),
    "NW": (-1, -1),
    "SE": (+1,  0),
    "SW": (+1, -1),
}

DIRECTIONS = list(_EVEN_DELTAS.keys())


@dataclass(frozen=True)
class TileData:
    row: int
    col: int


def hex_neighbors(row: int, col: int, rows: int, cols: int) -> dict[str, tuple[int, int]]:
    """Return the 6 neighbors of (row, col) with toroidal wrapping."""
    deltas = _EVEN_DELTAS if row % 2 == 0 else _ODD_DELTAS
    return {
        direction: ((row + dr) % rows, (col + dc) % cols)
        for direction, (dr, dc) in deltas.items()
    }


def generate_grid(rows: int, cols: int) -> list[TileData]:
    return [TileData(row=r, col=c) for r in range(rows) for c in range(cols)]
