from langgraph.graph import END, START, StateGraph

from nodes.narrator import narrator_node
from state import GraphState


class Graph:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)

    def build(self) -> StateGraph:
        self.workflow.add_node("narrator", narrator_node)
        self.workflow.add_edge(start_key=START, end_key="narrator")
        self.workflow.add_edge(start_key="narrator", end_key=END)
        return self.workflow
