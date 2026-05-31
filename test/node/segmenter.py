import pytest
from unittest.mock import patch, AsyncMock
from dspy.primitives.prediction import Prediction

from src.core.model.message import Message
from src.node.segmenter import SegmenterNode
from src.state import GraphState


def _state(human_text: str) -> GraphState:
    return GraphState(
        human_message=Message(role="human", content=human_text, name="player"),
        character_description="a wary scout",
        location_description="a quiet stone corridor",
        needs_roll=True,
    )


@pytest.mark.parametrize(
    "human_text,fake_output,expected",
    [
        # multi-beat with both preamble and tail
        (
            "I sprint across the courtyard, kill the archer at the top, then grab the crown.",
            ("I sprint across the courtyard", "kill the archer at the top", "grab the crown"),
            ("I sprint across the courtyard", "kill the archer at the top", "grab the crown"),
        ),
        # single contested beat, no preamble or tail
        (
            "I attack the bandit.",
            ("", "I attack the bandit.", ""),
            ("", "I attack the bandit.", ""),
        ),
        # preamble only, no tail
        (
            "I draw my blade and lunge at him.",
            ("I draw my blade", "lunge at him", ""),
            ("I draw my blade", "lunge at him", ""),
        ),
        # tail only, no preamble
        (
            "I cut the rope, then drop into the alley.",
            ("", "cut the rope", "drop into the alley"),
            ("", "cut the rope", "drop into the alley"),
        ),
        # whitespace handling
        (
            "I attack.",
            ("  ", "  I attack.  ", ""),
            ("", "I attack.", ""),
        ),
    ],
)
@pytest.mark.asyncio
async def test_segmenter_splits_message(human_text, fake_output, expected):
    lead_up, contested, tail = fake_output
    exp_lead, exp_contested, exp_tail = expected
    node = SegmenterNode()
    fake_prediction = Prediction(
        lead_up=lead_up, contested_beat=contested, deferred_tail=tail
    )
    with patch.object(node._program, "aforward", new=AsyncMock(return_value=fake_prediction)):
        result = await node(_state(human_text))
    assert result == {
        "lead_up": exp_lead,
        "contested_beat": exp_contested,
        "deferred_tail": exp_tail,
    }