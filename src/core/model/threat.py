from enum import IntEnum, StrEnum

class Channel(StrEnum):
    CORPUS = "corpus"
    MENS = "mens"
    ANIMA = "anima"

class Magnitude(IntEnum):
    MINOR = 1
    STANDARD = 2
    SEVERE = 3
    FATAL = 4
