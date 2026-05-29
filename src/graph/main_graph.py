from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.graph.intent_alignment_graph import IntentAlignmentGraphBuilder
from src.nodes.narrator import NarratorNode
from src.nodes.resolution import ResolutionNode
from src.nodes.roll_gate import RollGateNode
from src.state import GraphState


class MainGraphBuilder:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)
        self.intent_alignment_graph: CompiledStateGraph = IntentAlignmentGraphBuilder().build()

    def build(self) -> CompiledStateGraph:
        self.workflow.add_node("intent_alignment", self.intent_alignment_graph)
        self.workflow.add_node("roll_gate", RollGateNode())
        self.workflow.add_node("resolution", ResolutionNode())
        self.workflow.add_node("narrator", NarratorNode())

        self.workflow.add_edge(START, "intent_alignment")
        # Intent unclear -> end the turn on the clarifying question; don't roll/narrate.
        self.workflow.add_conditional_edges(
            source="intent_alignment",
            path=route_after_intent_alignment,
            path_map={True: "roll_gate", False: END},
        )
        # Roll only when the beat carries danger + uncertainty; else narrate directly.
        self.workflow.add_conditional_edges(
            source="roll_gate",
            path=route_after_roll_gate,
            path_map={True: "resolution", False: "narrator"},
        )
        self.workflow.add_edge("resolution", "narrator")
        self.workflow.add_edge("narrator", END)

        return self.workflow.compile()


def route_after_intent_alignment(state: GraphState) -> bool:
    return bool(state.is_intent_alignment_achieved)


def route_after_roll_gate(state: GraphState) -> bool:
    return bool(state.needs_roll)
