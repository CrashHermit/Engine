from src.state import GraphState


class TurnCloseNode:
    async def __call__(self, state: GraphState) -> dict:
        if state.human_message is not None and state.ai_message is not None:
            return {"message_history": [state.human_message, state.ai_message]}
        return {}
