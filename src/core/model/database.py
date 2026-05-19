from enum import Enum


class VertexType(Enum):
    SESSION = "SESSION"
    MESSAGE = "MESSAGE"

class EdgeType(Enum):
    HAS_MESSAGE = "HAS_MESSAGE"
    NEXT_MESSAGE = "NEXT_MESSAGE"