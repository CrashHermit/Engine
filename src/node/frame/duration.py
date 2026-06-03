from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.core.mechanic.duration import Span, Unit
from src.lm import lm
from src.state import GraphState


class DurationSignature(Signature):
    """
    You estimate how much *in-world time* the contested beat represents — the
    fictional duration that passes while this single action plays out. Pick the
    one rung on the ladder whose span best fits; you are not measuring seconds,
    you are choosing the closest bucket.

    - ROUND (~6s): a single decisive action or exchange — one strike, one leap,
      one quick line.
    - MOMENT (~30s): a brief flurry or quick back-and-forth.
    - MINUTE (~90s): a sustained effort or a short exchange of words.
    - SPELL (~5 min): searching a room, a real conversation, picking a lock.
    - STRETCH (~15 min): a thorough task, a tense negotiation.
    - HOUR: an hour of focused work.
    - WATCH (~4h): a guard shift, crossing a district, a long vigil.
    - NIGHT (~8h): sleeping, resting, a downtime block.
    - DAY: a full day passes.
    - WEEK / MONTH / YEAR: long spans — only when the fiction clearly skips
      ahead by that much.

    Most contested beats are short (ROUND to STRETCH). Pick a long rung only
    when the action itself spans that time ("I spend the night on watch",
    "I lie low until the heat dies down").
    """

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    entities_at_location: str = InputField(default="")
    contested_beat: str = InputField(
        description="The single contested action that needs a roll"
    )

    unit: Unit = OutputField(
        description="The ladder rung whose span best fits this beat"
    )


class DurationNode:
    """Reads the contested beat → how much fictional time it spans, as a single
    ladder rung (count 1). The world clock advances by this at turn close."""

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=DurationSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        entities = (
            "\n".join(state.entities_at_location) if state.entities_at_location else ""
        )
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=entities,
            contested_beat=state.contested_beat,
        )
        return {"beat_span": Span(Unit(prediction.unit))}
