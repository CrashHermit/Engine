"""Minimal seed eval sets for the framing classifiers (Phase 2).

The point of these is to establish a **metric before optimising** (design §10,
Phase 2): a small hand-labelled set per classifier and an exact-match metric, so
each module has a baseline number to improve against with `BootstrapFewShot` /
`MIPROv2` later. Deliberately tiny and hand-authored — bootstrapped expansion and
optimisation are a later, separate track.

Each case is `(inputs: dict, expected_label: str)`. `inputs` keys match the
classifier's signature input fields.
"""

from __future__ import annotations

from src.core.mechanics.magnitude import Magnitude
from src.core.model.resolution import Attribute, Effect, ThreatType

_CHAR = "A wiry sellsword, quick and clever, light on their feet."
_LOC = "A torchlit guardroom, stone underfoot, one barred door."
_NPC = "Guard: a heavyset watchman with a halberd. Location: blocking the door."


# Each entry: (inputs, expected). Inputs cover the signature's input fields.
ATTRIBUTE_CASES: list[tuple[dict, str]] = [
    ({"character_description": _CHAR, "location_description": _LOC,
      "contested_beat": "shoulder-barge the door off its hinges"}, Attribute.CORPUS),
    ({"character_description": _CHAR, "location_description": _LOC,
      "contested_beat": "decipher the faded runes carved above the arch"}, Attribute.MENS),
    ({"character_description": _CHAR, "location_description": _LOC,
      "contested_beat": "stare down the snarling hound until it backs off"}, Attribute.ANIMA),
    ({"character_description": _CHAR, "location_description": _LOC,
      "contested_beat": "vault the railing and sprint across the rooftop"}, Attribute.CORPUS),
]

EFFECT_CASES: list[tuple[dict, str]] = [
    ({"character_description": _CHAR, "location_description": _LOC, "entities_at_location": _NPC,
      "contested_beat": "pry the iron grate loose with bare hands"}, Effect.LIMITED),
    ({"character_description": _CHAR, "location_description": _LOC, "entities_at_location": "",
      "contested_beat": "pick the simple padlock with your tools"}, Effect.STANDARD),
    ({"character_description": _CHAR, "location_description": _LOC, "entities_at_location": "",
      "contested_beat": "ambush the lone sleeping sentry from behind"}, Effect.GREAT),
]

THREAT_TYPE_CASES: list[tuple[dict, str]] = [
    ({"character_description": _CHAR, "location_description": _LOC, "entities_at_location": _NPC,
      "contested_beat": "trade blows with the halberdier"}, ThreatType.HARM),
    ({"character_description": _CHAR, "location_description": _LOC, "entities_at_location": "",
      "contested_beat": "sneak past the patrol without being seen"}, ThreatType.WORSE_POSITION),
    ({"character_description": _CHAR, "location_description": _LOC, "entities_at_location": "",
      "contested_beat": "catch the falling chandelier before it shatters"}, ThreatType.FAILURE_OF_GOAL),
]

THREAT_MAGNITUDE_CASES: list[tuple[dict, int]] = [
    ({"character_description": _CHAR, "location_description": _LOC, "entities_at_location": "",
      "contested_beat": "squeeze through a gap and scrape your arm"}, int(Magnitude.MINOR)),
    ({"character_description": _CHAR, "location_description": _LOC, "entities_at_location": _NPC,
      "contested_beat": "duel the armed watchman in the open"}, int(Magnitude.SEVERE)),
    ({"character_description": _CHAR, "location_description": _LOC, "entities_at_location": "",
      "contested_beat": "leap the chasm over the lava flow"}, int(Magnitude.FATAL)),
]

THREAT_CHANNEL_CASES: list[tuple[dict, str]] = [
    ({"character_description": _CHAR, "location_description": _LOC, "entities_at_location": _NPC,
      "contested_beat": "take the halberd's swing head-on"}, Attribute.CORPUS),
    ({"character_description": _CHAR, "location_description": _LOC, "entities_at_location": "",
      "contested_beat": "resist the creeping dread of the haunted vault"}, Attribute.ANIMA),
    ({"character_description": _CHAR, "location_description": _LOC, "entities_at_location": "",
      "contested_beat": "avoid being fooled by the merchant's clever ruse"}, Attribute.MENS),
]
