from dataclasses import dataclass, field


@dataclass(slots=True)
class Position:
    x: float
    y: float
    z: float


@dataclass(slots=True)
class Cell:
    id: int
    position: Position
    neighbors: list[int] = field(default_factory=list)
