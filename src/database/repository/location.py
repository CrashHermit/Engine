from arcadedb_embedded.graph import Edge, Vertex

from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository

# Maps movement keys to compass directions.
KEY_DIRECTIONS: dict[str, str] = {
    "q": "NW", "w": "N", "e": "NE",
    "a": "SW", "s": "S", "d": "SE",
}

# Maps compass directions to their display key label.
DIRECTION_KEYS: dict[str, str] = {
    "NW": "Q", "N": "W", "NE": "E",
    "SW": "A", "S": "S", "SE": "D",
}

_COMPASS_ORDER = ["NW", "N", "NE", "SE", "S", "SW"]

# PROTOTYPE START
_HEX_NODES = [
    {
        "name": "The Crossroads Chamber",
        "description": (
            "A broad chamber where six passages meet. The ceiling is lost in shadow above. "
            "A rusted iron lantern hangs from a hook at the center of the room, its flame "
            "long dead. The air is cold and still."
        ),
        "is_center": True,
        "direction_from_center": None,
    },
    {
        "name": "The Collapsed Alcove",
        "description": (
            "A low-ceilinged alcove half-choked by fallen masonry. A crack runs the length "
            "of the far wall, black and deep. Water drips somewhere in the dark beyond."
        ),
        "is_center": False,
        "direction_from_center": "NW",
    },
    {
        "name": "The Long Corridor",
        "description": (
            "A narrow passage stretching into the dark. Torch brackets line the walls at "
            "even intervals, all empty. Boot marks in the dust suggest someone passed here, "
            "though not recently."
        ),
        "is_center": False,
        "direction_from_center": "N",
    },
    {
        "name": "The Bone Room",
        "description": (
            "Shelves of carved stone line the walls, still holding the remnants of old burial "
            "urns. Most have shattered. The floor is gritty underfoot. A low archway leads "
            "onward to the east."
        ),
        "is_center": False,
        "direction_from_center": "NE",
    },
    {
        "name": "The Flooded Antechamber",
        "description": (
            "The floor here is slick with a thin film of black water, fed by a seam in the "
            "wall. The smell is mineral and cold. An iron door, warped in its frame, stands "
            "sealed to the south."
        ),
        "is_center": False,
        "direction_from_center": "SE",
    },
    {
        "name": "The Guard Post",
        "description": (
            "A square room with a rotted wooden table and the remains of two stools. A rusted "
            "sword leans against one wall. Whatever was being guarded here, it was a long watch."
        ),
        "is_center": False,
        "direction_from_center": "S",
    },
    {
        "name": "The Pit Room",
        "description": (
            "The center of the floor has given way, leaving a dark hole roughly two paces "
            "across. Rope marks score the edge. There is no rope. There is no sound from below."
        ),
        "is_center": False,
        "direction_from_center": "SW",
    },
]

# Reverse of each compass direction.
_OPPOSITE: dict[str, str] = {
    "NW": "SE", "N": "S", "NE": "SW",
    "SE": "NW", "S": "N", "SW": "NE",
}

# Ring adjacencies between outer nodes (clockwise order: NW N NE SE S SW).
# Each tuple is (from_direction, to_direction, edge_direction).
_RING_EDGES: list[tuple[str, str, str]] = [
    ("NW", "N",  "NE"),
    ("N",  "NE", "SE"),
    ("NE", "SE", "S"),
    ("SE", "S",  "SW"),
    ("S",  "SW", "NW"),
    ("SW", "NW", "N"),
]


class LocationRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base = base

    def get_location(self, id: str) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.LOCATION, id=id)

    def create_location(self, name: str, description: str, is_center: bool = False) -> Vertex:
        return self._base.create_vertex(
            type_name=VertexType.LOCATION,
            name=name,
            description=description,
            is_center=is_center,
        )

    def connect_location(self, from_location: Vertex, to_location: Vertex, direction: str) -> Edge:
        return self._base.create_edge(
            type_name=EdgeType.CONNECTS,
            source=from_location,
            target=to_location,
            direction=direction,
        )

    def get_neighbor_in_direction(self, location: Vertex, direction: str) -> Vertex | None:
        for edge in location.get_out_edges(EdgeType.CONNECTS):
            if edge.get(name="direction") == direction:
                return edge.get_in()
        return None

    def get_exits(self, location: Vertex) -> list[str]:
        return [
            edge.get(name="direction")
            for edge in location.get_out_edges(EdgeType.CONNECTS)
            if edge.get(name="direction")
        ]

    # PROTOTYPE START
    def create_hex_graph(self) -> Vertex:
        """Create the 7-node dungeon hex graph. Returns the center vertex."""
        nodes: dict[str | None, Vertex] = {}

        for data in _HEX_NODES:
            vertex = self.create_location(
                name=data["name"],
                description=data["description"],
                is_center=data["is_center"],
            )
            nodes[data["direction_from_center"]] = vertex

        center = nodes[None]

        # Spoke edges: center ↔ each outer node
        for direction, outer in nodes.items():
            if direction is None:
                continue
            self.connect_location(center, outer, direction)
            self.connect_location(outer, center, _OPPOSITE[direction])

        # Ring edges: outer nodes ↔ their clockwise neighbors
        for from_dir, to_dir, edge_dir in _RING_EDGES:
            self.connect_location(nodes[from_dir], nodes[to_dir], edge_dir)
            self.connect_location(nodes[to_dir], nodes[from_dir], _OPPOSITE[edge_dir])

        return center
    # PROTOTYPE END
