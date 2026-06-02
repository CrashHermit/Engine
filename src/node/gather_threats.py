from src.state import GraphState

class GatherThreatsNode:
    """Fan-in: move the accumulated pending_threats (built by the parallel
    classify branches) into the plain `threats` list that dice_scale and the
    resist cycle overwrite."""

    async def __call__(self, state: GraphState) -> dict:
        return {"threats": list(state.pending_threats)}