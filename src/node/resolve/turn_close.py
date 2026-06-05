from src.state import GraphState


class TurnCloseNode:
    async def __call__(self, state: GraphState) -> dict:
        if state.get("human_message") is not None and state.get("ai_message") is not None:
            return {"message_history": [state.get("human_message"), state.get("ai_message")]}
        return {}
