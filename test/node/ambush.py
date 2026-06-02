import pytest

from src.core.mechanic.magnitude import Magnitude
from src.core.mechanic.scaling import Position
from src.core.model.message import Message
from src.core.model.threat import Channel, Threat, ThreatType
from src.node.threat.ambush import AmbushNode
from src.node.threat.ambush_scale import AmbushScaleNode
from src.state import GraphState


@pytest.mark.asyncio
async def test_ambush_node_marks_turn_and_seeds_beat():
    state = GraphState(human_message=Message(role="human", content="I study the old map", name=""))
    result = await AmbushNode()(state)
    assert result["is_ambush"] is True
    assert result["contested_beat"] == "I study the old map"


def _threat(mag: Magnitude) -> Threat:
    return Threat(
        source="Spider",
        type=ThreatType.HARM,
        channel=Channel.CORPUS,
        magnitude=mag,
        position=Position.DESPERATE,
    )


@pytest.mark.asyncio
async def test_ambush_scale_lands_threats_at_full():
    state = GraphState(threats=[_threat(Magnitude.SEVERE), _threat(Magnitude.MINOR)])
    result = await AmbushScaleNode()(state)
    outcomes = [t.outcome for t in result["threats"]]
    assert [o.landed_magnitude for o in outcomes] == [Magnitude.SEVERE, Magnitude.MINOR]
    assert all(not o.avoided and not o.crit for o in outcomes)
    # all landed (>= MINOR) → feed the resist cycle
    assert len(GraphState(threats=result["threats"]).landed_threats) == 2


@pytest.mark.asyncio
async def test_ambush_scale_empty_is_noop_list():
    result = await AmbushScaleNode()(GraphState(threats=[]))
    assert result["threats"] == []
