import dspy

from core.model.message import Message
from module.narrator import NarratorModule
from module.utils import format_messages
from nodes.base import BaseNode
from state import GraphState


class NarratorNode(BaseNode[GraphState]):
    def __init__(self) -> None:
        super().__init__(
            module_class=NarratorModule,
            node_name="narrator",
            output_field="ai_message",
        )

    def get_inputs(self, state: GraphState) -> dict:
        return {
            "message_history": format_messages(state.message_history),
            "human_message": state.human_message.content,
        }

    def build_update(self, state: GraphState, prediction: dspy.Prediction) -> dict:
        ai_message = Message(
            role="ai",
            content=prediction.ai_message.strip(),
            name="Narrator",
        )
        return {
            "message_history": [state.human_message, ai_message],
            "ai_message": ai_message,
        }
