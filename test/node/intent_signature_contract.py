from __future__ import annotations

import dspy
import pytest

from src.core.model.message import Message
from src.node.intent.alignment_router import IntentAlignmentRouterNode
from src.node.intent.question_generator import IntentQuestionGeneratorNode
from src.node.intent.synthesizer import IntentSynthesizerNode
from src.state import GraphState


def _state() -> GraphState:
    # Non-empty alignment history so the synthesizer takes its LLM path.
    return GraphState(
        human_message=Message(role="human", content="open the door", name="Vale"),
        intent_alignment_history=[Message(role="ai", content="which door?", name="IA")],
        character_name="Vale",
        character_description="a scout",
        location_name="Courtyard",
        location_description="a quiet yard",
        entities_at_location=["Door: oak. Location: north"],
        message_history=[],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "node_cls, output",
    [
        (IntentAlignmentRouterNode, {"is_intent_alignment_achieved": True}),
        (IntentQuestionGeneratorNode, {"question": "which one?"}),
        (IntentSynthesizerNode, {"synthesized_message": "I open the north door"}),
    ],
)
async def test_intent_node_passes_only_declared_inputs(node_cls, output):
    """Verify every kwarg a node hands to aforward is a declared signature input.

    Otherwise DSPy silently drops the data (the character_name/location_name
    mismatch this guards against).
    """
    node = node_cls()
    captured: dict = {}

    async def fake_aforward(**kwargs):
        captured.update(kwargs)
        return dspy.Prediction(**output)

    node._program.aforward = fake_aforward
    await node(_state())

    declared = set(node._program.signature.input_fields)
    extra = set(captured) - declared
    assert not extra, f"{node_cls.__name__} passes undeclared inputs: {sorted(extra)}"
    # And the names are actually wired through now.
    assert captured.get("character_name") == "Vale"
    assert captured.get("location_name") == "Courtyard"
