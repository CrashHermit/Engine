from typing import Annotated

from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from module import NarratorModule


class GraphState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

class Graph:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)
        self.narrator_module: NarratorModule = NarratorModule()

    async def narrator_node(self, state: GraphState) -> dict:
        messages = state["messages"]
        human_message = messages[-1]
        response: AIMessage = self.narrator_module.aforward(
            chat_history=messages,
            message=human_message,
        )
        return {"messages": [response]}

    def build(self) -> StateGraph:
        self.workflow.add_node("narrator", self.narrator_node)
        self.workflow.add_edge(START, "narrator")
        self.workflow.add_edge("narrator", END)
        return self.workflow
