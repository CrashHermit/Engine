from src.core.mechanic.narration_directive import mundane_directive
from src.state import GraphState


class MundaneNode:
    async def __call__(self, state: GraphState) -> dict:
        return {"narration_directive": mundane_directive(state.get("lead_up") or "")}
