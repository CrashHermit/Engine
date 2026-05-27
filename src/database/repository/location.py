from arcadedb_embedded.graph import Edge, Vertex

from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository


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

    def connect_locations(self, a: Vertex, b: Vertex) -> Edge:
        return self._base.create_edge(
            type_name=EdgeType.CONNECTS,
            source=a,
            target=b,
        )

    def get_neighbors(self, location: Vertex) -> list[Vertex]:
        neighbors = []
        for edge in location.get_both_edges(EdgeType.CONNECTS):
            if edge.get_out().get_rid() == location.get_rid():
                neighbors.append(edge.get_in())
            else:
                neighbors.append(edge.get_out())
        return neighbors

        # PROTOTYPE START
    def create_start_location(self) -> Vertex:
        """Create the 7-node dungeon hex graph. Returns the center vertex."""
        nodes = [
            self.create_location(name=n["name"], description=n["description"], is_center=n["is_center"])
            for n in _HEX_NODES
        ]
        center = nodes[0]
        for outer in nodes[1:]:
            self.connect_locations(center, outer)
        for a, b in _RING_PAIRS:
            self.connect_locations(nodes[a], nodes[b])
        return center
    # PROTOTYPE END



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
    },
    {
        "name": "The Collapsed Alcove",
        "description": (
            "A low-ceilinged alcove half-choked by fallen masonry. A crack runs the length "
            "of the far wall, black and deep. Water drips somewhere in the dark beyond."
        ),
        "is_center": False,
    },
    {
        "name": "The Long Corridor",
        "description": (
            "A narrow passage stretching into the dark. Torch brackets line the walls at "
            "even intervals, all empty. Boot marks in the dust suggest someone passed here, "
            "though not recently."
        ),
        "is_center": False,
    },
    {
        "name": "The Bone Room",
        "description": (
            "Shelves of carved stone line the walls, still holding the remnants of old burial "
            "urns. Most have shattered. The floor is gritty underfoot. A low archway leads "
            "onward to the east."
        ),
        "is_center": False,
    },
    {
        "name": "The Flooded Antechamber",
        "description": (
            "The floor here is slick with a thin film of black water, fed by a seam in the "
            "wall. The smell is mineral and cold. An iron door, warped in its frame, stands "
            "sealed to the south."
        ),
        "is_center": False,
    },
    {
        "name": "The Guard Post",
        "description": (
            "A square room with a rotted wooden table and the remains of two stools. A rusted "
            "sword leans against one wall. Whatever was being guarded here, it was a long watch."
        ),
        "is_center": False,
    },
    {
        "name": "The Pit Room",
        "description": (
            "The center of the floor has given way, leaving a dark hole roughly two paces "
            "across. Rope marks score the edge. There is no rope. There is no sound from below."
        ),
        "is_center": False,
    },
]

# Ring adjacency pairs by index into _HEX_NODES (nodes 1-6 form the outer ring).
_RING_PAIRS = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1)]


