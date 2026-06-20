from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.core.mechanic.duration import Duration, Unit
from src.lm import lm
from src.state import GraphState


class DurationSignature(Signature):
    """You estimate how much *in-world time* the contested beat represents.

    The fictional duration that passes while this single action plays out.
    Pick the one ladder rung whose span best fits — you are not measuring
    seconds, you are choosing the closest bucket. Return the rung's exact
    unit name (snake_case).

    Short rungs (most contested beats land here):
    - six_seconds (~6s): a quick reaction or combat round — one strike, leap,
      or line.
    - thirty_seconds (~30s): a brief physical exchange or quick back-and-forth.
    - one_minute (~1 min): a quick search, lockpick, or short effort.
    - five_minutes (~5 min): bandaging, a short rest, picking a lock under
      pressure.
    - ten_minutes (~10 min): a focused conversation, ritual, or room search.
    - fifteen_minutes (~15 min): a thorough task or tense negotiation.
    - thirty_minutes (~30 min): a half-hour of work or a short meal.
    - one_hour: standard travel, study, or focused work.
    - two_hours: a long meeting, movie-length vigil, or extended effort.
    - four_hours: a guard watch, crossing a district, half a workday.
    - eight_hours: a full workday, night's sleep, or downtime block.
    - twelve_hours: dawn to dusk, half a day.

    Long rungs — only when the fiction clearly skips ahead by that much
    ("I spend the night on watch", "I lie low until the heat dies down"):
    - one_day, three_days, one_week, two_weeks, three_weeks, one_month,
      three_months, six_months, one_year.

    Default short. Pick a long rung only when the action itself spans it.
    """

    contested_beat: str = InputField(
        description="The single contested action that needs a roll"
    )

    unit: Unit = OutputField(
        description=(
            "Exact ladder rung name (snake_case) whose span best fits this beat"
        )
    )


class DurationNode:
    """Read the contested beat and determine how much fictional time it spans.

    Returns a single ladder rung. The world clock advances by this at turn close.
    """

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=DurationSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        prediction: Prediction = await self._program.aforward(
            contested_beat=state.get("contested_beat", ""),
        )
        return {"beat_span": Duration(Unit(prediction.unit))}
