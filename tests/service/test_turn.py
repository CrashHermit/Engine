from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.model.character import CharacterData
from src.core.model.location import LocationData, LocationState
from src.core.model.message import Message
from src.service.turn import CompletedResult, PausedResult, TurnContext, TurnService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _character() -> CharacterData:
    return CharacterData(
        id="char-1",
        name="Silas",
        description="A scarred duelist",
        corpus=2,
        mens=2,
        anima=2,
        extraversion=3,
        openness=3,
        agreeableness=3,
        neuroticism=3,
        conscientiousness=3,
    )


def _location_state() -> LocationState:
    return LocationState(
        location=LocationData(id="loc-1", name="The Crow's Nest", description="A rickety watchtower"),
        neighbors=[],
        entities=[],
    )


def _ctx(run_id: str = "run-abc") -> TurnContext:
    return TurnContext(
        character=_character(),
        location_state=_location_state(),
        message_history=[],
        run_id=run_id,
    )


def _graph_service(*, result: dict, paused: bool = False) -> MagicMock:
    svc = MagicMock()
    svc.thread_config.return_value = {"configurable": {"thread_id": "w:char-1:run-abc"}}
    svc.is_paused = AsyncMock(return_value=paused)
    svc.ainvoke = AsyncMock(return_value=result)
    svc.resume = AsyncMock(return_value=result)
    svc.interrupt_question = MagicMock(return_value=None)
    svc.new_run_id = MagicMock(return_value="run-next")
    return svc


def _service(graph_svc: MagicMock) -> TurnService:
    return TurnService(
        graph_service=graph_svc,
        character=MagicMock(),
        location=MagicMock(),
        world_name="test-world",
    )


# ---------------------------------------------------------------------------
# GraphState construction
# ---------------------------------------------------------------------------


class TestBuildState:
    async def test_state_fields_come_from_context(self) -> None:
        """run_turn passes a GraphState built from TurnContext to ainvoke."""
        ai_msg = Message(role="ai", content="Steel rings off steel.", name="")
        graph_svc = _graph_service(result={"ai_message": ai_msg, "message_history": [ai_msg]})
        svc = _service(graph_svc)

        await svc.run_turn("I lunge!", _ctx())

        state = graph_svc.ainvoke.call_args.args[0]
        assert state.character_name == "Silas"
        assert state.character_description == "A scarred duelist"
        assert state.location_name == "The Crow's Nest"
        assert state.human_message.content == "I lunge!"
        assert state.message_history == []
        assert state.intent_alignment_history == []

    async def test_entities_at_location_are_formatted(self) -> None:
        from src.core.model.location import EntityData

        loc = LocationState(
            location=LocationData(id="loc-1", name="Docks", description="Wet planks"),
            neighbors=[],
            entities=[EntityData(name="Guard", description="Armed.", scene_position="doorway")],
        )
        ctx = TurnContext(character=_character(), location_state=loc, message_history=[], run_id="r")
        ai_msg = Message(role="ai", content=".", name="")
        graph_svc = _graph_service(result={"ai_message": ai_msg, "message_history": []})
        svc = _service(graph_svc)

        await svc.run_turn("look around", ctx)

        state = graph_svc.ainvoke.call_args.args[0]
        assert state.entities_at_location == ["Guard: Armed.. Location: doorway"]

    async def test_missing_location_state_yields_empty_fields(self) -> None:
        ctx = TurnContext(
            character=_character(), location_state=None, message_history=[], run_id="r"
        )
        ai_msg = Message(role="ai", content=".", name="")
        graph_svc = _graph_service(result={"ai_message": ai_msg, "message_history": []})
        svc = _service(graph_svc)

        await svc.run_turn("wait", ctx)

        state = graph_svc.ainvoke.call_args.args[0]
        assert state.location_name == ""
        assert state.location_description == ""
        assert state.entities_at_location == []


# ---------------------------------------------------------------------------
# Effect dispatch (skeleton — no effects fields yet)
# ---------------------------------------------------------------------------


class TestEffectDispatch:
    async def test_no_service_writes_when_graph_has_no_effect_fields(self) -> None:
        """Effect application is a no-op today; underlying services are never written to."""
        ai_msg = Message(role="ai", content="You wait.", name="")
        graph_svc = _graph_service(result={"ai_message": ai_msg, "message_history": []})
        character_svc = MagicMock()
        location_svc = MagicMock()
        svc = TurnService(graph_svc, character_svc, location_svc, "w")

        await svc.run_turn("wait", _ctx())

        character_svc.assert_not_called()
        location_svc.assert_not_called()


# ---------------------------------------------------------------------------
# Resume path / interrupt handling
# ---------------------------------------------------------------------------


class TestResumePath:
    async def test_resume_returns_paused_when_graph_re_interrupts(self) -> None:
        """If the graph interrupts again during resume, PausedResult is returned."""
        graph_svc = _graph_service(result={"__interrupt__": [MagicMock(value={"question": "Clarify?"})]})
        graph_svc.interrupt_question = MagicMock(return_value="Clarify?")
        svc = _service(graph_svc)

        result = await svc.resume_turn("I meant the guard", _ctx())

        assert isinstance(result, PausedResult)
        assert result.question == "Clarify?"

    async def test_resume_calls_graph_resume_not_ainvoke(self) -> None:
        """resume_turn drives the graph via resume(), not a fresh ainvoke()."""
        ai_msg = Message(role="ai", content="You slip past.", name="")
        graph_svc = _graph_service(result={"ai_message": ai_msg, "message_history": [ai_msg]})
        svc = _service(graph_svc)

        await svc.resume_turn("yes, the guard", _ctx())

        graph_svc.resume.assert_called_once()
        graph_svc.ainvoke.assert_not_called()

    async def test_resume_returns_completed_result_on_success(self) -> None:
        """A clean resume with narration produces CompletedResult."""
        ai_msg = Message(role="ai", content="You slip past.", name="")
        graph_svc = _graph_service(result={"ai_message": ai_msg, "message_history": [ai_msg]})
        svc = _service(graph_svc)

        result = await svc.resume_turn("yes, the guard", _ctx())

        assert isinstance(result, CompletedResult)
        assert result.narration == "You slip past."
        assert result.message_history == [ai_msg]
        assert result.next_run_id == "run-next"
