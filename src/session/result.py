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
class TurnError:
    """A turn failed; submit() is total and yields this instead of raising."""

    message: str


TurnEvent = ClarifyingQuestion | Narration | ResistanceOffer | TurnError
