import uuid
import logging
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command, StateSnapshot
from langgraph.graph.state import CompiledStateGraph

from src.graph.main_graph import MainGraphBuilder
from src.logging_utils import summarize_mapping
from src.state import GraphState


class GraphService:
    def __init__(self, checkpointer: BaseCheckpointSaver) -> None:
        self._logger = logging.getLogger("engine.service.graph")
        self.checkpointer = checkpointer
        self.graph: CompiledStateGraph = MainGraphBuilder(checkpointer=checkpointer).build()
        self._logger.info("graph service initialized")

    @staticmethod
    def new_run_id() -> str:
        return uuid.uuid4().hex

    def thread_config(self, *, world_name: str, character_id: str, run_id: str) -> dict:
        config = {
            "configurable": {
                "thread_id": f"{world_name}:{character_id}:{run_id}",
            }
        }
        self._logger.debug("thread config created: %s", summarize_mapping(config["configurable"]))
        return config

    async def ainvoke(self, input: GraphState | Command, *, config: dict) -> dict:
        self._logger.debug(
            "ainvoke start thread=%s input=%s",
            config.get("configurable", {}).get("thread_id"),
            type(input).__name__,
        )
        result = await self.graph.ainvoke(input, config=config)
        self._logger.debug("ainvoke result keys=%s", list(result.keys()) if isinstance(result, dict) else [])
        return result

    async def aget_state(self, *, config: dict) -> StateSnapshot:
        return await self.graph.aget_state(config=config)

    async def is_paused(self, *, config: dict) -> bool:
        snapshot = await self.aget_state(config=config)
        paused = bool(snapshot.next)
        self._logger.debug(
            "pause check thread=%s paused=%s",
            config.get("configurable", {}).get("thread_id"),
            paused,
        )
        return paused

    @staticmethod
    def interrupt_question(result: dict) -> str | None:
        """Pull the clarifying question out of a paused result.

        When the intent alignment subgraph pauses via ``interrupt()``, the
        question lives in the interrupt payload (not the parent graph's
        top-level state), so we read it from there.
        """
        interrupts = result.get("__interrupt__")
        if not interrupts:
            return None
        payload = interrupts[0].value
        if isinstance(payload, dict):
            return payload.get("question")
        return str(payload)

    @staticmethod
    def interrupt_offer(result: dict) -> str | None:
        """Pull the resistance offer out of a paused result.

        When ``ResistOfferNode`` pauses via ``interrupt()``, the offer text
        lives in the payload under the ``"offer"`` key.
        """
        interrupts = result.get("__interrupt__")
        if not interrupts:
            return None
        payload = interrupts[0].value
        if isinstance(payload, dict):
            return payload.get("offer")
        return None

    async def resume(self, answer: str, *, config: dict) -> dict:
        self._logger.debug(
            "resume thread=%s answer=%s",
            config.get("configurable", {}).get("thread_id"),
            answer[:120],
        )
        return await self.graph.ainvoke(Command(resume=answer), config=config)
