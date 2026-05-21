import dspy
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.messages.utils import get_buffer_string

from module.base import StreamingDSPyNode
from state import GraphState

lm: dspy.LM = dspy.LM(
    model="openrouter/google/gemma-4-26b-a4b-it",
    api_key="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",
    temperature=0.7,
)
dspy.configure(lm=lm)


class NarratorSignature2(dspy.Signature):
    """
    You are a narrator, you will take the input from the human and the chat history and you will return the narration of the message.
    """

    message_history: str = dspy.InputField(default="", description="The chat history")
    human_message: str = dspy.InputField(
        default=HumanMessage(content="", name=""),
        description="The message to predict",
    )
    ai_message: str = dspy.OutputField(
        default="", description="The narration of the message"
    )


class NarratorModule2(StreamingDSPyNode):
    def __init__(self) -> None:
        super().__init__(node_name="narrator", output_field="ai_message")
        self.narrator_prediction: dspy.ChainOfThought = dspy.ChainOfThought(
            signature=NarratorSignature2
        )

    async def aforward(
        self, message_history: list[BaseMessage], human_message: HumanMessage
    ) -> dspy.Prediction:
        return await self.narrator_prediction.acall(
            message_history=get_buffer_string(messages=message_history),
            human_message=get_buffer_string(messages=[human_message]),
        )

    async def narrator_node(self, state: GraphState) -> dict:
        prediction: dspy.Prediction = await self.stream_to_writer(
            message_history=state["message_history"],
            human_message=state["human_message"],
        )
        ai_message: AIMessage = AIMessage(
            content=prediction.ai_message.strip(), name="Narrator"
        )
        return {
            "message_history": [ai_message],
            "ai_message": ai_message,
        }
