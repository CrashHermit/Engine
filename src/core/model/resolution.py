"""Domain vocabulary for the resolution pipeline (decisions #5, #15, #18).

Small, broad, classifier-friendly taxonomies — one label per judgment. Kept here
beside the other domain models so signatures, nodes, and the mechanics core all
share the same words.
"""

from enum import StrEnum


class Attribute(StrEnum):
    """The three broad attributes a roll can draw on (decision #1)."""

    CORPUS = "corpus"  # body — physical force, endurance, dexterity
    MENS = "mens"      # mind — reason, perception, knowledge
    ANIMA = "anima"    # spirit — will, presence, social, instinct


class Effect(StrEnum):
    """How much a success accomplishes within the resolved beat."""

    LIMITED = "limited"
    STANDARD = "standard"
    GREAT = "great"


class ThreatType(StrEnum):
    """What kind of consequence a less-than-clean roll brings (decision #15)."""

    HARM = "harm"
    COMPLICATION = "complication"
    WORSE_POSITION = "worse_position"
    LOST_OPPORTUNITY = "lost_opportunity"
    FAILURE_OF_GOAL = "failure_of_goal"
