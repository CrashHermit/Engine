import uuid
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command, StateSnapshot
from langgraph.graph.state import CompiledStateGraph

from src.graph.main_graph import MainGraphBuilder
from src.state import GraphState


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

    async def ainvoke(self, input: GraphState | Command, *, config: dict) -> dict:
        return await self.graph.ainvoke(input, config=config)

    async def aget_state(self, *, config: dict) -> StateSnapshot:
        return await self.graph.aget_state(config=config)

    async def is_paused(self, *, config: dict) -> bool:
        snapshot = await self.aget_state(config=config)
        return bool(snapshot.next)

    async def resume(self, answer: str, *, config: dict) -> dict:
        return await self.graph.ainvoke(Command(resume=answer), config=config)
