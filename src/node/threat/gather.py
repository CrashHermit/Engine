from src.state import GraphState


class GatherThreatsNode:
    """Fan-in: move accumulated pending_threats into the plain threats list.

    The pending_threats are built by the parallel classify branches. The
    threats list is what dice_scale and the resist cycle overwrite.
    """

    async def __call__(self, state: GraphState) -> dict:
        return {"threats": list(state.get("pending_threats", []))}
