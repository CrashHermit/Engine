from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from dspy.primitives.prediction import Prediction

from src.core.model.message import Message
from src.node.frame.roll_gate import RollGateNode
from src.state import GraphState


def _state(human_text: str) -> GraphState:
    return GraphState(
        human_message=Message(role="human", content=human_text, name="player"),
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
    with patch.object(
        node._program, "aforward", new=AsyncMock(return_value=fake_prediction)
    ):
        result = await node(_state(human_text))
    assert result["needs_roll"] == expected
    # On the no-roll (mundane) path the node also carries the player's message
    # forward as the lead_up for narration; on the roll path it does not.
    if expected:
        assert "lead_up" not in result
    else:
        assert result["lead_up"] == human_text
