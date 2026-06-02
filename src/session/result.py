from dataclasses import dataclass

# Typed turn events yielded by GameCoordinator.submit. Each carries plain
# strings only — no Rich markup. The TUI maps each variant to a styled write
# (decision: presentation lives in the display layer). A single turn may yield
# several events in order; the resistance path yields Narration (the held
# narration) followed by ResistanceOffer.


@dataclass(frozen=True)
class ClarifyingQuestion:
    """Intent-alignment subgraph paused asking the player to clarify intent."""

    question: str


@dataclass(frozen=True)
class Narration:
    """Narrator prose for the resolved beat."""

    text: str


@dataclass(frozen=True)
class ResistanceOffer:
    """The turn paused offering resistance; the player's next message resumes it."""

    offer: str


@dataclass(frozen=True)
class TraumaGained:
    """A stress overflow converted to trauma this turn. Carries the new trauma
    total so the display can show progress toward the cap."""

    trauma: int


@dataclass(frozen=True)
class CharacterLost:
    """The character hit the trauma cap and is lost (retired/dead/broken)."""


@dataclass(frozen=True)
class TargetDefeated:
    """The action broke the target's EXISTS pillar; it is destroyed and removed
    from the scene. Carries the entity name for display."""

    name: str


@dataclass(frozen=True)
class TargetSuspended:
    """The action broke a non-lethal pillar (will, awareness, reach, capability);
    the target is out of the scene but not destroyed. Carries the entity name."""

    name: str


@dataclass(frozen=True)
class TargetReturned:
    """A suspended creature re-engaged this turn (its broken pillar reverted)."""

    name: str


@dataclass(frozen=True)
class TurnError:
    """A turn failed; submit() is total and yields this instead of raising."""

    message: str


TurnEvent = (
    ClarifyingQuestion
    | Narration
    | ResistanceOffer
    | TraumaGained
    | CharacterLost
    | TargetDefeated
    | TargetSuspended
    | TargetReturned
    | TurnError
)
