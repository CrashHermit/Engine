from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.graph.intent_alignment_graph import IntentAlignmentGraphBuilder
from src.nodes.action_generator import ActionGeneratorNode
from src.nodes.narrator import NarratorNode
from src.state import GraphState


class MainGraphBuilder:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)
        self.intent_alignment_graph: CompiledStateGraph = IntentAlignmentGraphBuilder().build()

    def build(self) -> CompiledStateGraph:
        self.workflow.add_node("intent_alignment", self.intent_alignment_graph)
        self.workflow.add_node("action_generator", ActionGeneratorNode())
        self.workflow.add_node("narrator", NarratorNode())

        self.workflow.add_edge(START, "intent_alignment")
        self.workflow.add_edge("intent_alignment", "action_generator")
        self.workflow.add_edge("action_generator", "narrator")
        self.workflow.add_edge("narrator", END)

        return self.workflow.compile()
