from src.worldgen.data import DungeonData, EntityGen, LocationGen, WorldData


# PROTOTYPE: a fixed 7-node hex dungeon used as every world's starting area.
# This will be replaced by procedural generation driven by world parameters.
class DungeonStage:
    def run(self, data: WorldData) -> WorldData:
        locations = [
            LocationGen(
                name=node["name"],
                description=node["description"],
                is_center=node["is_center"],
                entities=[
                    EntityGen(
                        name=entity["name"],
                        description=entity["description"],
                        scene_position=entity["scene_position"],
                    )
                    for entity in node["entities"]
                ],
            )
            for node in _HEX_NODES
        ]

        # Center (index 0) connects to each outer node, plus the outer ring.
        connections: list[tuple[int, int]] = [(0, i) for i in range(1, len(locations))]
        connections.extend(_RING_PAIRS)

        data.dungeon = DungeonData(locations=locations, connections=connections)
        return data


_HEX_NODES = [
    {
        "name": "The Crossroads Chamber",
        "description": (
            "A broad chamber where six passages meet. The ceiling is lost in shadow above. "
            "A rusted iron lantern hangs from a hook at the center of the room, its flame "
            "long dead. The air is cold and still."
        ),
        "is_center": True,
        "entities": [
            {
                "name": "Dead Lantern",
                "description": "A rusted iron lantern with a cracked glass pane. The oil reservoir is bone dry and the wick has long since burned away.",
                "scene_position": "hanging from an iron hook at the center of the ceiling",
            },
            {
                "name": "Iron Hook",
                "description": "A thick iron hook bolted into the ceiling stone, worn smooth by years of use. It could bear weight.",
                "scene_position": "mounted at the center of the ceiling, above the lantern",
            },
        ],
    },
    {
        "name": "The Collapsed Alcove",
        "description": (
            "A low-ceilinged alcove half-choked by fallen masonry. A crack runs the length "
            "of the far wall, black and deep. Water drips somewhere in the dark beyond."
        ),
        "is_center": False,
        "entities": [
            {
                "name": "Fallen Masonry",
                "description": "Heavy chunks of worked stone and mortar, some the size of a man's torso. The collapse looks old.",
                "scene_position": "piled from floor to ceiling across the back half of the alcove",
            },
            {
                "name": "Wall Crack",
                "description": "A vertical fissure running the full height of the far wall. It is wide enough to fit a hand into, and utterly dark beyond.",
                "scene_position": "running floor to ceiling along the far wall behind the rubble",
            },
            {
                "name": "Large Aggressive Spider (Ready to Strike)",
                "description": "A large aggressive spider, about the size of a man's torso, is crawling along the wall. Ready to strike and attack at any moment.",
                "scene_position": "crawling along the wall",
            }
        ],
    },
    {
        "name": "The Long Corridor",
        "description": (
            "A narrow passage stretching into the dark. Torch brackets line the walls at "
            "even intervals, all empty. Boot marks in the dust suggest someone passed here, "
            "though not recently."
        ),
        "is_center": False,
        "entities": [
            {
                "name": "Empty Torch Bracket",
                "description": "A wrought-iron bracket fixed to the stone wall. The socket is caked with old soot but holds nothing.",
                "scene_position": "mounted on the right wall at head height, midway down the corridor",
            },
            {
                "name": "Boot Prints",
                "description": "Faint impressions pressed into a thin layer of dust on the floor. Two sets, heading in the same direction. Not recent.",
                "scene_position": "running along the center of the corridor floor",
            },
        ],
    },
    {
        "name": "The Bone Room",
        "description": (
            "Shelves of carved stone line the walls, still holding the remnants of old burial "
            "urns. Most have shattered. The floor is gritty underfoot. A low archway leads "
            "onward to the east."
        ),
        "is_center": False,
        "entities": [
            {
                "name": "Shattered Burial Urn",
                "description": "A ceramic funerary urn, cracked along the base and split open. Whatever it held has long since mixed with the dust on the floor.",
                "scene_position": "lying on its side on the lowest stone shelf to the left of the entrance",
            },
            {
                "name": "Stone Shelf",
                "description": "A long shelf carved directly from the wall, roughly hewn. Several intact urns remain, sealed with wax that has gone black and brittle.",
                "scene_position": "lining the right wall from knee height to the ceiling",
            },
        ],
    },
    {
        "name": "The Flooded Antechamber",
        "description": (
            "The floor here is slick with a thin film of black water, fed by a seam in the "
            "wall. The smell is mineral and cold. An iron door, warped in its frame, stands "
            "sealed to the south."
        ),
        "is_center": False,
        "entities": [
            {
                "name": "Warped Iron Door",
                "description": "A heavy iron door swollen in its frame, sealed by rust and pressure. The hinges are fused. A keyhole sits empty on the right side.",
                "scene_position": "set into the south wall, flush with the stone",
            },
            {
                "name": "Wall Seam",
                "description": "A long horizontal crack in the north wall weeping a thin trickle of black water that spreads across the floor.",
                "scene_position": "running along the north wall at ankle height",
            },
        ],
    },
    {
        "name": "The Guard Post",
        "description": (
            "A square room with a rotted wooden table and the remains of two stools. A rusted "
            "sword leans against one wall. Whatever was being guarded here, it was a long watch."
        ),
        "is_center": False,
        "entities": [
            {
                "name": "Rotted Table",
                "description": "A wooden table gone soft with damp and age. The surface bows under its own weight. Something has gnawed one of the legs.",
                "scene_position": "at the center of the room",
            },
            {
                "name": "Rusted Sword",
                "description": "A short blade of corroded iron, the grip wrapped in leather that has stiffened and split. The edge is pitted but might still hold.",
                "scene_position": "leaning point-down against the east wall",
            },
        ],
    },
    {
        "name": "The Pit Room",
        "description": (
            "The center of the floor has given way, leaving a dark hole roughly two paces "
            "across. Rope marks score the edge. There is no rope. There is no sound from below."
        ),
        "is_center": False,
        "entities": [
            {
                "name": "Dark Pit",
                "description": "A ragged hole where the floor has collapsed. The edges are crumbling. No light reaches the bottom. No sound rises from it either.",
                "scene_position": "at the center of the room",
            },
            {
                "name": "Rope Marks",
                "description": "Deep parallel grooves worn into the stone lip of the pit, left by a rope under heavy load. Whatever used the rope last did not leave it behind.",
                "scene_position": "scored into the north edge of the pit",
            },
        ],
    },
]

# Outer-ring adjacency pairs by index into _HEX_NODES (nodes 1-6 form the ring).
_RING_PAIRS = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1)]
