from langgraph.graph import END, START, StateGraph

from src.nodes.narrator import NarratorNode
from src.nodes.clarity_router import ClarityRouterNode
from src.nodes.clarity_generator import ClarityGeneratorNode
from src.state import GraphState


class Graph:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)

    def build(self) -> StateGraph:
        self.workflow.add_node("narrator", NarratorNode())
        self.workflow.add_node("clarity_router", ClarityRouterNode())
        self.workflow.add_node("clarity_generator", ClarityGeneratorNode())

        self.workflow.add_edge(start_key=START, end_key="clarity_router")
        self.workflow.add_conditional_edges(
            start_key="clarity_router",
            path="is_clarity_achieved",
            path_map={
                True: "narrator",
                False: "clarity_generator",
            },

        )
        self.workflow.add_edge(start_key="clarity_generator", end_key="clarity_router")
        self.workflow.add_edge(start_key="narrator", end_key=END)
        return self.workflow
