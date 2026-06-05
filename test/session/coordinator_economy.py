from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src.core.model.character import CharacterData
from src.core.model.location import EntityData, LocationData, LocationState
from src.core.model.message import Message
from src.session.coordinator import GameCoordinator
from src.session.result import CharacterLost, Narration, TraumaGained


def _character(stress: int = 0, trauma: int = 0) -> CharacterData:
    return CharacterData(
        id="char-1",
        name="Vale",
        description="a wary scout",
        corpus=2,
        mens=1,
        anima=1,
        extraversion=2,
        openness=2,
        agreeableness=2,
        neuroticism=2,
        conscientiousness=2,
        stress=stress,
        trauma=trauma,
    )


def _location_state() -> LocationState:
    return LocationState(
        location=LocationData(
            id="loc-1", name="Courtyard", description="a quiet stone yard"
        ),
        neighbors=[],
        entities=[
            EntityData(name="Guard", description="armed", scene_position="by the gate")
        ],
    )


def _coordinator(
    *, character: CharacterData, result: dict
) -> tuple[GameCoordinator, Mock]:
    run_ids = iter([f"run-{i}" for i in range(10)])
    graph = SimpleNamespace(
        new_run_id=lambda: next(run_ids),
        thread_config=lambda **kwargs: {"configurable": {"thread_id": "t"}},
        is_paused=AsyncMock(return_value=False),
        ainvoke=AsyncMock(return_value=result),
        resume=AsyncMock(return_value=result),
    )
    set_economy = Mock()
    services = SimpleNamespace(
        graph_service=graph,
        location=SimpleNamespace(
            get_state_for_character=lambda character_id: _location_state(),
            move_character=lambda character_id, destination_id: _location_state(),
        ),
        character=SimpleNamespace(set_economy=set_economy),
        time=SimpleNamespace(now=lambda: 0, advance=lambda delta: 0),
        world_name="world",
    )
    return GameCoordinator(character=character, services=services), set_economy


def _ai(content: str) -> Message:
    return Message(role="ai", content=content, name="Narrator")


@pytest.mark.asyncio
async def test_submit_seeds_stress_and_trauma_into_graph_state():
    coord, _ = _coordinator(
        character=_character(stress=4, trauma=1),
        result={
            "ai_message": _ai("done"),
            "message_history": [],
            "stress": 4,
            "trauma": 1,
        },
    )
    [e async for e in coord.submit("look around")]

    sent_state = coord._services.graph_service.ainvoke.await_args.args[0]
    assert sent_state["stress"] == 4
    assert sent_state["trauma"] == 1


@pytest.mark.asyncio
async def test_submit_persists_changed_economy():
    character = _character(stress=0, trauma=0)
    coord, set_economy = _coordinator(
        character=character,
        result={
            "ai_message": _ai("ouch"),
            "message_history": [],
            "stress": 7,
            "trauma": 0,
        },
    )
    events = [e async for e in coord.submit("strike")]

    assert events == [Narration("ouch")]
    set_economy.assert_called_once_with("char-1", stress=7, trauma=0)
    assert character.stress == 7


@pytest.mark.asyncio
async def test_submit_does_not_persist_when_economy_unchanged():
    coord, set_economy = _coordinator(
        character=_character(stress=3, trauma=0),
        result={
            "ai_message": _ai("calm"),
            "message_history": [],
            "stress": 3,
            "trauma": 0,
        },
    )
    [e async for e in coord.submit("wait")]

    set_economy.assert_not_called()


@pytest.mark.asyncio
async def test_submit_surfaces_trauma_gained():
    coord, set_economy = _coordinator(
        character=_character(stress=8, trauma=0),
        result={
            "ai_message": _ai("snap"),
            "message_history": [],
            "stress": 0,
            "trauma": 1,
            "trauma_gained": True,
        },
    )
    events = [e async for e in coord.submit("push on")]

    assert events == [Narration("snap"), TraumaGained(1)]
    set_economy.assert_called_once_with("char-1", stress=0, trauma=1)


@pytest.mark.asyncio
async def test_submit_surfaces_character_lost_at_trauma_cap():
    coord, _ = _coordinator(
        character=_character(stress=8, trauma=3),
        result={
            "ai_message": _ai("end"),
            "message_history": [],
            "stress": 0,
            "trauma": 4,
            "trauma_gained": True,
            "character_lost": True,
        },
    )
    events = [e async for e in coord.submit("push on")]

    assert events == [Narration("end"), TraumaGained(4), CharacterLost()]
