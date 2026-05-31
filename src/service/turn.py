from dataclasses import dataclass

from src.core.model.character import CharacterData
from src.core.model.location import LocationState
from src.core.model.message import Message
from src.service.character import CharacterService
from src.service.graph import GraphService
from src.service.location import LocationService
from src.state import GraphState


@dataclass(frozen=True)
class TurnContext:
    character: CharacterData
    location_state: LocationState | None
    message_history: list[Message]
    run_id: str


@dataclass(frozen=True)
class PausedResult:
    question: str


@dataclass(frozen=True)
class CompletedResult:
    narration: str
    message_history: list[Message]
    next_run_id: str


TurnResult = PausedResult | CompletedResult


class TurnService:
    def __init__(
        self,
        graph_service: GraphService,
        character: CharacterService,
        location: LocationService,
        world_name: str,
    ) -> None:
        self._graph = graph_service
        self._character = character
        self._location = location
        self._world_name = world_name

    async def is_paused(self, ctx: TurnContext) -> bool:
        return await self._graph.is_paused(config=self._config(ctx))

    async def run_turn(self, text: str, ctx: TurnContext) -> TurnResult:
        result = await self._graph.ainvoke(self._build_state(text, ctx), config=self._config(ctx))
        return self._process(result, ctx)

    async def resume_turn(self, text: str, ctx: TurnContext) -> TurnResult:
        result = await self._graph.resume(text, config=self._config(ctx))
        return self._process(result, ctx)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _config(self, ctx: TurnContext) -> dict:
        return self._graph.thread_config(
            world_name=self._world_name,
            character_id=ctx.character.id,
            run_id=ctx.run_id,
        )

    def _build_state(self, text: str, ctx: TurnContext) -> GraphState:
        loc = ctx.location_state
        entities = (
            [f"{e.name}: {e.description}. Location: {e.scene_position}" for e in loc.entities]
            if loc is not None
            else []
        )
        return GraphState(
            message_history=ctx.message_history,
            intent_alignment_history=[],
            human_message=Message(role="human", content=text, name=""),
            ai_message=None,
            question=None,
            is_intent_alignment_achieved=None,
            character_name=ctx.character.name,
            character_description=ctx.character.description,
            location_name=loc.location.name if loc else "",
            location_description=loc.location.description if loc else "",
            entities_at_location=entities,
        )

    def _process(self, result: dict, ctx: TurnContext) -> TurnResult:
        question = self._graph.interrupt_question(result)
        if question is not None:
            return PausedResult(question=question)

        ai_msg = result.get("ai_message")
        narration = ""
        if ai_msg is not None:
            narration = ai_msg.content if hasattr(ai_msg, "content") else ai_msg.get("content", "")

        message_history: list[Message] = result.get("message_history", ctx.message_history)

        # TODO: apply effects from state (harm, stress, trauma) once GraphState carries them.

        return CompletedResult(
            narration=narration,
            message_history=message_history,
            next_run_id=self._graph.new_run_id(),
        )
