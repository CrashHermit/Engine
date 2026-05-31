import uuid
from typing import TYPE_CHECKING, Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command, StateSnapshot

from src.graph.main_graph import MainGraphBuilder
from src.state import GraphState

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


class GraphService:
    def __init__(self, checkpointer: BaseCheckpointSaver) -> None:
        self.checkpointer = checkpointer
        self.graph: CompiledStateGraph = MainGraphBuilder(checkpointer=checkpointer).build()

    @staticmethod
    def new_run_id() -> str:
        return uuid.uuid4().hex

    def thread_config(self, *, world_name: str, character_id: str, run_id: str) -> dict:
        return {
            "configurable": {
                "thread_id": f"{world_name}:{character_id}:{run_id}",
            }
        }

    async def ainvoke(self, input: GraphState | Command, *, config: dict) -> dict[str, Any]:
        return await self.graph.ainvoke(input, config=config)

    async def aget_state(self, *, config: dict[str, Any]) -> StateSnapshot:
        return await self.graph.aget_state(config=config)

    async def is_paused(self, *, config: dict) -> bool:
        snapshot = await self.aget_state(config=config)
        return bool(snapshot.next)

    @staticmethod
    def interrupt_question(result: dict[str, Any]) -> str | None:
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

    async def resume(self, answer: str, *, config: dict) -> dict[str, Any]:
        return await self.graph.ainvoke(Command(resume=answer), config=config)
