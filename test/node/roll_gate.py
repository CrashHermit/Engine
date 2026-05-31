import pytest
from unittest.mock import patch, AsyncMock
from dspy.primitives.prediction import Prediction

from src.core.model.message import Message
from src.node.roll_gate import RollGateNode
from src.state import GraphState


def _state(human_text: str) -> GraphState:
    return GraphState(
        human_message=Message(role="human", content=human_text, name="player"),
        character_description="a wary scout",
        location_description="a quiet stone corridor",
    )


@pytest.mark.parametrize(
    "human_text,gate_output,expected",
    [
        ("I walk to the next room.", False, False),
        ("I sprint across the courtyard while archers fire.", True, True),
        ("I open the unlocked door.", False, False),
        ("I try to leap the chasm in full armor.", True, True),
    ],
)
@pytest.mark.asyncio
async def test_roll_gate_returns_needs_roll(human_text, gate_output, expected):
    node = RollGateNode()
    fake_prediction = Prediction(needs_roll=gate_output)
    with patch.object(node._program, "aforward", new=AsyncMock(return_value=fake_prediction)):
        result = await node(_state(human_text))
    assert result == {"needs_roll": expected}