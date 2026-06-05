from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.core.mechanic.duration import TICKS, Span, Unit
from src.core.model.character import CharacterData
from src.core.model.location import EntityData, LocationData, LocationState
from src.core.model.message import Message
from src.core.model.threat import Channel
from src.session.coordinator import GameCoordinator
from src.session.result import ClarifyingQuestion, Narration, ResistanceOffer, TurnError
from src.state import pool_for


def _character() -> CharacterData:
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
    )


def _location_state() -> LocationState:
    return LocationState(
        location=LocationData(
            id="loc-1", name="Courtyard", description="a quiet stone yard"
        ),
        neighbors=[LocationData(id="loc-2", name="Hall", description="a long hall")],
        entities=[
            EntityData(name="Guard", description="armed", scene_position="by the gate")
        ],
    )


def _fake_graph_service(*, paused: bool, result: dict) -> SimpleNamespace:
    run_ids = iter(["run-1", "run-2", "run-3"])
    return SimpleNamespace(
        new_run_id=lambda: next(run_ids),
        thread_config=lambda **kwargs: {"configurable": {"thread_id": "t"}},
        is_paused=AsyncMock(return_value=paused),
        ainvoke=AsyncMock(return_value=result),
        resume=AsyncMock(return_value=result),
    )


class _FakeClock:
    """Stand in for TimeService in memory: now() reads, advance() accumulates."""

    def __init__(self) -> None:
        self.ticks = 0
        self.advances: list[int] = []

    def now(self) -> int:
        return self.ticks

    def advance(self, delta: int) -> int:
        self.advances.append(delta)
        if delta > 0:
            self.ticks += delta
        return self.ticks


def _fake_services(
    graph_service: SimpleNamespace, location: SimpleNamespace
) -> SimpleNamespace:
    return SimpleNamespace(
        graph_service=graph_service,
        location=location,
        time=_FakeClock(),
        world_name="world",
    )


def _coordinator(*, paused: bool = False, result: dict) -> GameCoordinator:
    graph = _fake_graph_service(paused=paused, result=result)
    location = SimpleNamespace(
        get_state_for_character=lambda character_id: _location_state(),
        move_character=lambda character_id, destination_id: _location_state(),
    )
    services = _fake_services(graph, location)
    return GameCoordinator(character=_character(), services=services)


def _interrupt(value: dict) -> dict:
    return {"__interrupt__": [SimpleNamespace(value=value)]}


def _ai(content: str) -> Message:
    return Message(role="ai", content=content, name="Narrator")


@pytest.mark.asyncio
async def test_submit_yields_clarifying_question_without_rotating_run_id():
    coord = _coordinator(result=_interrupt({"question": "Which guard?"}))
    before = coord._run_id

    events = [e async for e in coord.submit("attack the guard")]

    assert events == [ClarifyingQuestion("Which guard?")]
    assert coord._run_id == before


@pytest.mark.asyncio
async def test_submit_yields_held_narration_then_offer_without_rotating_run_id():
    # The held narration is carried in the interrupt payload, not in
    # result["ai_message"] — the resolution subgraph's ai_message does not
    # propagate to the parent result while paused on the resist interrupt.
    result = _interrupt(
        {"offer": "Resist and twist aside?", "narration": "The blade bites deep."}
    )
    coord = _coordinator(result=result)
    before = coord._run_id

    events = [e async for e in coord.submit("strike")]

    assert events == [
        Narration("The blade bites deep."),
        ResistanceOffer("Resist and twist aside?"),
    ]
    assert coord._run_id == before


@pytest.mark.asyncio
async def test_submit_yields_narration_and_rotates_run_id_on_completion():
    result = {"ai_message": _ai("You slip past unseen."), "message_history": [_ai("x")]}
    coord = _coordinator(result=result)
    before = coord._run_id

    events = [e async for e in coord.submit("sneak past")]

    assert events == [Narration("You slip past unseen.")]
    assert coord._run_id != before


@pytest.mark.asyncio
async def test_submit_seeds_attribute_ratings_into_graph_state():
    # _character() has corpus=2, mens=1, anima=1 — these must reach the graph
    # so the action and resist rolls use the real pools, not a zero pool.
    result = {"ai_message": _ai("done"), "message_history": []}
    coord = _coordinator(result=result)

    [e async for e in coord.submit("strike")]

    sent_state = coord._services.graph_service.ainvoke.await_args.args[0]
    assert pool_for(sent_state, Channel.CORPUS) == 2
    assert pool_for(sent_state, Channel.MENS) == 1
    assert pool_for(sent_state, Channel.ANIMA) == 1


@pytest.mark.asyncio
async def test_submit_yields_turn_error_when_invoke_raises():
    coord = _coordinator(result={})
    coord._services.graph_service.ainvoke = AsyncMock(
        side_effect=RuntimeError("graph boom")
    )

    events = [e async for e in coord.submit("do a thing")]

    assert events == [TurnError("graph boom")]


@pytest.mark.asyncio
async def test_submit_resumes_when_paused():
    result = {"ai_message": _ai("Resolved."), "message_history": []}
    coord = _coordinator(paused=True, result=result)

    events = [e async for e in coord.submit("I twist aside")]

    coord._services.graph_service.resume.assert_awaited_once()
    coord._services.graph_service.ainvoke.assert_not_awaited()
    assert events == [Narration("Resolved.")]


@pytest.mark.asyncio
async def test_submit_seeds_world_clock_into_graph_state():
    result = {"ai_message": _ai("done"), "message_history": []}
    coord = _coordinator(result=result)
    coord._services.time.ticks = 4800  # mid-game world clock

    [e async for e in coord.submit("strike")]

    sent_state = coord._services.graph_service.ainvoke.await_args.args[0]
    assert sent_state["elapsed_ticks"] == 4800


@pytest.mark.asyncio
async def test_completed_turn_advances_world_clock_by_beat_span():
    span = Span(Unit.WEEK, 2)
    result = {
        "ai_message": _ai("time passes"),
        "message_history": [],
        "beat_span": span,
    }
    coord = _coordinator(result=result)

    [e async for e in coord.submit("lie low a while")]

    assert coord._services.time.advances == [span.ticks]


@pytest.mark.asyncio
async def test_completed_turn_without_beat_span_advances_one_round():
    result = {"ai_message": _ai("a quick strike"), "message_history": []}
    coord = _coordinator(result=result)

    [e async for e in coord.submit("strike")]

    assert coord._services.time.advances == [TICKS[Unit.ROUND]]


def test_enter_stores_and_returns_location():
    coord = _coordinator(result={})

    state = coord.enter()

    assert state is not None
    assert coord.current_location is state
    assert state.location.name == "Courtyard"


def test_move_updates_current_location():
    coord = _coordinator(result={})

    state = coord.move("loc-2")

    assert state is not None
    assert coord.current_location is state
