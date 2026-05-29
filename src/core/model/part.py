from enum import StrEnum


class Shape(StrEnum):
    CYLINDRICAL = "cylindrical"
    SPHERICAL = "spherical"
    RECTANGULAR = "rectangular"
    CUBOID = "cuboid"
    SQUARE = "square"
    ELLIPSOID = "ellipsoid"
    CONICAL = "conical"
    IRREGULAR = "irregular"


class Status(StrEnum):
    NORMAL = "normal"
    COMPROMISED = "compromised"
    CRITICAL = "critical"
    DESTROYED = "destroyed"  # part lost; detaches from the body graph (decision #19)


class SizeScale(StrEnum):
    MICROSCOPIC = "microscopic"  # cell / bacteria
    MINIATURE = "miniature"      # fingernail / coin
    TINY = "tiny"                # finger / thumb
    SMALL = "small"              # hand / foot
    SLIGHT = "slight"            # child / large dog
    MEDIUM = "medium"            # full human body
    TOWERING = "towering"        # horse / large humanoid
    LARGE = "large"              # car / elephant
    HUGE = "huge"                # building / whale
    COLOSSAL = "colossal"        # skyscraper / mountain
    TITANIC = "titanic"          # island / continent


class PartFunction(StrEnum):
    SOURCE = "source"
    SINK = "sink"
    STORAGE = "storage"
    MANIPULATOR = "manipulator"
    MOVEMENT = "movement"
    OPENING = "opening"
    CHANNEL = "channel"
    CONTROLLABLE = "controllable"
