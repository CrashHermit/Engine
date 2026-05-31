from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.graph.intent_alignment_graph import IntentAlignmentGraphBuilder
from src.node.action_generator import ActionGeneratorNode
from src.node.narrator import NarratorNode
from src.node.roll_gate import RollGateNode
from src.node.segmenter import SegmenterNode
from src.state import GraphState


def route_by_roll_gate(state: GraphState) -> str:
    return "segmenter" if state.needs_roll else "narrator"


class MainGraphBuilder:
    def __init__(self, *, checkpointer: BaseCheckpointSaver) -> None:
        self._checkpointer: BaseCheckpointSaver = checkpointer
        self.workflow: StateGraph = StateGraph(GraphState)
        self.intent_alignment_graph: CompiledStateGraph = IntentAlignmentGraphBuilder().build()

    def build(self) -> CompiledStateGraph:
        self.workflow.add_node("intent_alignment", self.intent_alignment_graph)
        self.workflow.add_node("roll_gate", RollGateNode())
        self.workflow.add_node("segmenter", SegmenterNode())
        self.workflow.add_node("action_generator", ActionGeneratorNode())
        self.workflow.add_node("narrator", NarratorNode())

        self.workflow.add_edge(start_key=START, end_key="intent_alignment")
        self.workflow.add_edge(start_key="intent_alignment", end_key="roll_gate")
        self.workflow.add_conditional_edges(
            source="roll_gate",
            path=route_by_roll_gate,
        )
        self.workflow.add_edge(start_key="segmenter", end_key="action_generator")
        self.workflow.add_edge(start_key="action_generator", end_key="narrator")
        self.workflow.add_edge(start_key="narrator", end_key=END)

        return self.workflow.compile(checkpointer=self._checkpointer)