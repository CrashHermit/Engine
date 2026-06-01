import asyncio
from collections.abc import AsyncIterator

from src.core.model.character import CharacterData
from src.core.model.location import LocationState
from src.core.model.message import Message
from src.service.container import ServiceContainer
from src.session.result import (
    ClarifyingQuestion,
    Narration,
    ResistanceOffer,
    TurnError,
    TurnEvent,
)
from src.state import GraphState

# The integration boundary (design decision #21). GameCoordinator owns turn
# orchestration and all graph-shape translation, so the TUI only displays. It
# is Textual-free and unit-testable with a faked GraphService. Effect
# persistence (harm/stress via services after ainvoke) will slot into submit()
# in a later PR; for now this is a behaviour-preserving relocation of the logic
# that lived on GameScreen.


def _interrupt_payload(result: dict) -> dict | str | None:
    """The value of the first interrupt on a paused graph result, if any."""
    interrupts = result.get("__interrupt__")
    if not interrupts:
        return None
    return interrupts[0].value


def _interrupt_question(result: dict) -> str | None:
    """Clarifying question from a paused intent-alignment result, if present.

    The question lives in the interrupt payload, not the top-level state.
    """
    payload = _interrupt_payload(result)
    if payload is None:
        return None
    if isinstance(payload, dict):
        return payload.get("question")
    return str(payload)


def _interrupt_offer(result: dict) -> str | None:
    """Resistance offer from a paused ResistOfferNode result, if present."""
    payload = _interrupt_payload(result)
    if isinstance(payload, dict):
        return payload.get("offer")
    return None


def _interrupt_narration(result: dict) -> str | None:
    """Held narration carried in a paused ResistOfferNode payload, if present.

    The narrator runs inside the resolution subgraph, so its ai_message does
    not surface in the parent graph result while the subgraph is paused on the
    resist interrupt. The held prose is therefore carried in the interrupt
    payload, not in result["ai_message"]."""
    payload = _interrupt_payload(result)
    if isinstance(payload, dict):
        return payload.get("narration")
    return None


def _message_content(ai_msg: object) -> str:
    """Pull text out of an ai_message that may be a Message or a plain dict."""
    if hasattr(ai_msg, "content"):
        return ai_msg.content
    return ai_msg.get("content", "")


class GameCoordinator:
    """Owns a single character's play session: location, turn carry, and the
    graph turn loop. Talks to services only; never to Textual or repositories."""

    def __init__(self, *, character: CharacterData, services: ServiceContainer) -> None:
        self._character = character
        self._services = services
        self._location_state: LocationState | None = None
        self._message_history: list[Message] = []
        # One thread per in-progress action. Reused while clarifying intent,
        # rotated once an action completes so the next action starts fresh.
        self._run_id = self._services.graph_service.new_run_id()
        # Reserved for the deferred-tail hint (decision #10); not yet populated.
        self._pending_intent: str | None = None
        self._lock = asyncio.Lock()

    @property
    def character(self) -> CharacterData:
        return self._character

    @property
    def current_location(self) -> LocationState | None:
        return self._location_state

    def enter(self) -> LocationState | None:
        """Fetch and store the character's starting location state."""
        state = self._services.location.get_state_for_character(self._character.id)
        if state is not None:
            self._location_state = state
        return state

    def move(self, destination_id: str) -> LocationState | None:
        """Move to a connected location and store the new state."""
        state = self._services.location.move_character(self._character.id, destination_id)
        if state is not None:
            self._location_state = state
        return state

    async def submit(self, text: str) -> AsyncIterator[TurnEvent]:
        """Run one turn, yielding ordered turn events. Total: never raises.

        A pending interrupt on this thread means we are mid-clarification, so
        this message is the player's answer; otherwise it is a new action.
        """
        async with self._lock:
            graph_service = self._services.graph_service
            config = graph_service.thread_config(
                world_name=self._services.world_name,
                character_id=self._character.id,
                run_id=self._run_id,
            )
            try:
                resuming = await graph_service.is_paused(config=config)
                if resuming:
                    result = await graph_service.resume(text, config=config)
                else:
                    result = await graph_service.ainvoke(
                        self._build_graph_state(text), config=config
                    )

                question = _interrupt_question(result)
                if question is not None:
                    # Turn still in progress; do NOT rotate run_id.
                    yield ClarifyingQuestion(question)
                    return

                offer = _interrupt_offer(result)
                if offer is not None:
                    # Held narration is carried in the interrupt payload (the
                    # subgraph's ai_message does not reach the parent result
                    # while paused) — emit the consequence before the offer.
                    narration = _interrupt_narration(result)
                    if narration:
                        yield Narration(narration)
                    # Turn still in progress; do NOT rotate run_id.
                    yield ResistanceOffer(offer)
                    return

                ai_msg = result.get("ai_message")
                if ai_msg is not None:
                    self._message_history = result.get("message_history", self._message_history)
                    yield Narration(_message_content(ai_msg))
                else:
                    yield Narration("")

                # Action finished; next message starts a brand-new thread.
                self._run_id = graph_service.new_run_id()
            except Exception as e:
                yield TurnError(str(e))

    def _build_graph_state(self, text: str) -> GraphState:
        state = self._location_state
        entities_at_location = (
            [f"{e.name}: {e.description}. Location: {e.scene_position}" for e in state.entities]
            if state is not None
            else []
        )
        return GraphState(
            message_history=self._message_history,
            intent_alignment_history=[],
            human_message=Message(role="human", content=text, name=""),
            ai_message=None,
            question=None,
            is_intent_alignment_achieved=None,
            character_name=self._character.name or "",
            character_description=self._character.description or "",
            location_name=state.location.name if state else "",
            location_description=state.location.description if state else "",
            entities_at_location=entities_at_location,
        )
