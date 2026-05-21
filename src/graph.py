from langchain_core.messages.human import HumanMessage


from langchain_core.messages.utils import AnyMessage


from typing import Annotated

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from module import NarratorModule


class GraphState(TypedDict):
    message_history: Annotated[list[AnyMessage], add_messages]
    clarity_history: Annotated[list[AnyMessage], add_messages]
    human_message: HumanMessage
    ai_message: AIMessage

class Graph:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)
        self.narrator_module: NarratorModule = NarratorModule()

    async def narrator_node(self, state: GraphState) -> dict:
        message_history: list[AnyMessage] = state["message_history"]
        human_message: HumanMessage = state["human_message"]
        
        ai_message: AIMessage = self.narrator_module.aforward(
            message_history=message_history,
            human_message=human_message,
        )
        
        return {
            "message_history": [human_message, ai_message],
            "ai_message": ai_message,
        }

    async def clarity_checker_node(self, state: GraphState) -> dict:
        message_history: list[AnyMessage] = state["message_history"]
        clarity_history: list[AnyMessage] = state["clarity_history"]
        human_message: HumanMessage = state["human_message"]
        
        clarity_checker_message: AIMessage = self.clarity_checker_module.aforward(
            message_history=message_history,
            clarity_history=clarity_history,
            human_message=human_message,

    def build(self) -> StateGraph:
        self.workflow.add_node("narrator", self.narrator_node)
        self.workflow.add_edge(start_key=START, end_key="narrator")
        self.workflow.add_edge(start_key="narrator", end_key=END)
        return self.workflow
