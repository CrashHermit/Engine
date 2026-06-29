from dataclasses import dataclass, field


@dataclass(slots=True)
class Tile:
    id: int
    x: float
    y: float
    z: float
    neighbors: list[int] = field(default_factory=list)

    elevation: float = 0.0
