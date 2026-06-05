from __future__ import annotations

from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.lm import lm
from src.state import GraphState


class TargetSignature(Signature):
    """Identify the target of the contested beat.

    The target is the entity the action is directed at (the foe being struck,
    the lock being forced). Return its exact name from the listed entities, or
    an empty string if the action targets no specific entity (movement,
    perception, environment).
    """

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    entities_at_location: str = InputField(default="")
    contested_beat: str = InputField(
        description="The single contested action that needs a roll"
    )

    target: str = OutputField(
        description=(
            "Exact name of the entity the action is directed at, or empty "
            "string if none (movement, perception, environment)."
        )
    )


class TargetNode:
    """Reads which entity the action is aimed at.

    Code-derives the unambiguous cases — no entities present → no target; a
    single entity → that one — and only spends an LLM call to disambiguate when
    two or more entities could be the target. apply_effect acts only on CREATURE
    targets, so a derived object/none target safely no-ops downstream.
    """

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=TargetSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        candidates = state.get("scene_entities", [])
        if len(candidates) <= 1:
            return {"target_entity": candidates[0].name if candidates else ""}

        entities = (
            "\n".join(state.get("entities_at_location", []))
            if state.get("entities_at_location", [])
            else ""
        )
        prediction: Prediction = await self._program.aforward(
            character_description=state.get("character_description", ""),
            location_description=state.get("location_description", ""),
            entities_at_location=entities,
            contested_beat=state.get("contested_beat", ""),
        )
        return {"target_entity": (prediction.target or "").strip()}
