import uuid
from langgraph.checkpoint.base import BaseCheckpointSaver

class GraphService:
    def __init__(self, checkpointer: BaseCheckpointSaver) -> None:
        pass

    @staticmethod
    def new_run_id() -> str:
        return uuid.uuid4().hex

    def thread_config(self, *, world_name: str, character_id: str, run_id: str) -> dict:
        pass

    async def ainvoke(self, input: GraphState | Command, *, config: dict) -> dict[str, Any]:
        pass

    async def aget_state(self, *, config: dict):
        pass

    async def is_paused(self, *, config: dict) -> bool:
        pass

    async def resume(self, update: dict, *, config: dict) -> dict[str, Any]:
        pass