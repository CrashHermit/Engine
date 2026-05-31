from enum import StrEnum


class Channel(StrEnum):
    CORPUS = "corpus"
    MENS = "mens"
    ANIMA = "anima"


class ThreatType(StrEnum):
    HARM = "harm"
    COMPLICATION = "complication"
    WORSE_POSITION = "worse_position"
    LOST_OPPORTUNITY = "lost_opportunity"
    FAILURE_OF_GOAL = "failure_of_goal"