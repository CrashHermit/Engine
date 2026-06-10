from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SavageryBand(StrEnum):
    TAME = "tame"
    BENIGN = "benign"
    PLACID = "placid"
    WILD = "wild"
    RUGGED = "rugged"
    SAVAGE = "savage"
    PRIMAL = "primal"

@dataclass(frozen=True)
class SavageryBandInfo:
    label: str
    description: str
    flavor: list[str]


ORDER: tuple[SavageryBand, ...] = (
    SavageryBand.TAME,
    SavageryBand.BENIGN,
    SavageryBand.PLACID,
    SavageryBand.WILD,
    SavageryBand.RUGGED,
    SavageryBand.SAVAGE,
    SavageryBand.PRIMAL,
)

BREAKPOINTS: tuple[float, ...] = (1/7, 2/7, 3/7, 4/7, 5/7, 6/7)

INFO: dict[SavageryBand, SavageryBandInfo] = {
    SavageryBand.TAME: SavageryBandInfo(
        label="Tame",
        description=(
            "Land worn smooth by habit and husbandry. The wild has retreated "
            "to hedgerows and ditches; what moves here is expected."
        ),
        flavor=[
            "Hedgerows trimmed back from the road.",
            "Woodsmoke hangs low and familiar.",
            "Birdsong follows a predictable hour.",
            "Paths are rutted but deliberate.",
            "A dog barks once and settles again.",
        ],
    ),
    SavageryBand.BENIGN: SavageryBandInfo(
        label="Benign",
        description=(
            "Gentle country where beasts are small or shy. Danger exists, "
            "but it feels like an exception rather than the rule."
        ),
        flavor=[
            "Rabbits scatter at footfall, not at thought.",
            "Moss muffles every step.",
            "Insects hum without malice.",
            "Berry thickets lean toward the sun.",
            "The wind passes through, not against.",
        ],
    ),
    SavageryBand.PLACID: SavageryBandInfo(
        label="Placid",
        description=(
            "Quiet wilds that ask little of travelers. Life goes about its "
            "business with indifference rather than hunger."
        ),
        flavor=[
            "Leaves drift down without hurry.",
            "A stream finds its old course unchallenged.",
            "Deer watch, then return to grazing.",
            "Spiderwebs hold the morning intact.",
            "Nothing tracks you for long.",
        ],
    ),
    SavageryBand.WILD: SavageryBandInfo(
        label="Wild",
        description=(
            "Honest wilderness — recognizable, uneven, and sometimes cruel. "
            "What lives here follows rules you could learn with time."
        ),
        flavor=[
            "Undergrowth snags cloth and patience.",
            "Calls echo from somewhere unseen.",
            "Tracks cross your path and move on.",
            "Weather turns without consultation.",
            "Old game trails end in uncertainty.",
        ],
    ),
    SavageryBand.RUGGED: SavageryBandInfo(
        label="Rugged",
        description=(
            "Harder country where distance, terrain, or temperament raise the "
            "cost of every mile. The land tolerates you; it does not welcome you."
        ),
        flavor=[
            "Stone outcrops like clenched teeth.",
            "Wind finds every gap in your gear.",
            "Scrub claws at exposed skin.",
            "Something large moved here recently.",
            "Silence has weight in the high ground.",
        ],
    ),
    SavageryBand.SAVAGE: SavageryBandInfo(
        label="Savage",
        description=(
            "Untamed reaches where size, strangeness, and temper flare. "
            "Giants and odd folk are plausible; ordinary caution may not suffice."
        ),
        flavor=[
            "Trees grow thick enough to hide a hall.",
            "A call answers your call — not human.",
            "Broken branches mark a passage too wide for deer.",
            "Eyes in the treeline, unafraid.",
            "The air tastes of iron and sap.",
        ],
    ),
    SavageryBand.PRIMAL: SavageryBandInfo(
        label="Primal",
        description=(
            "Mythic wilds at the edge of credence. The land feels older than "
            "maps; what stirs here belongs to story more than field guide."
        ),
        flavor=[
            "Footprints deepen into something you refuse to name.",
            "Flowers bloom where nothing should root.",
            "The horizon bends around a presence.",
            "Every sound arrives twice.",
            "Even the stones seem to listen.",
        ],
    ),
}