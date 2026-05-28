from langgraph.graph import END, START, StateGraph

from src.nodes.narrator import NarratorNode
from src.state import GraphState


class Graph:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)

    def build(self) -> StateGraph:
        self.workflow.add_node("narrator", NarratorNode())
        self.workflow.add_edge(start_key=START, end_key="narrator")
        self.workflow.add_edge(start_key="narrator", end_key=END)
        return self.workflow
