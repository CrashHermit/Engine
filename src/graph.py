from typing import Annotated

import dspy
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from module import NarratorModule2


class GraphState(TypedDict):
    message_history: Annotated[list[AnyMessage], add_messages]
    clarity_history: Annotated[list[AnyMessage], add_messages]
    human_message: HumanMessage
    ai_message: AIMessage


class Graph:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)
        self.narrator_module: NarratorModule2 = NarratorModule2()

    async def narrator_node(self, state: GraphState) -> dict:
        message_history: list[AnyMessage] = state["message_history"]
        human_message: HumanMessage = state["human_message"]
        ai_message: AIMessage | None = None
        streamed_tokens = False
        async for chunk in self.narrator_module.stream(
            message_history=message_history,
            human_message=human_message,
        ):
            if isinstance(chunk, dspy.streaming.StreamResponse):
                streamed_tokens = True
                print(chunk.chunk, end="", flush=True)
            elif isinstance(chunk, dspy.Prediction):
                content = chunk.ai_message.strip()
                ai_message = AIMessage(content=content, name="Narrator")
                if not streamed_tokens:
                    print(content, end="", flush=True)
        if ai_message is not None:
            print()
        return {
            "message_history": [ai_message],
            "ai_message": ai_message,
        }

    def build(self) -> StateGraph:
        self.workflow.add_node("narrator", self.narrator_node)
        self.workflow.add_edge(start_key=START, end_key="narrator")
        self.workflow.add_edge(start_key="narrator", end_key=END)
        return self.workflow
