from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.graph.intent_alignment_graph import IntentAlignmentGraphBuilder
from src.node.action_generator import ActionGeneratorNode
from src.node.narrator import NarratorNode
from src.node.roll_gate import RollGateNode
from src.state import GraphState


class MainGraphBuilder:
    def __init__(self, *, checkpointer: BaseCheckpointSaver) -> None:
        self._checkpointer: BaseCheckpointSaver = checkpointer
        self.workflow: StateGraph = StateGraph(GraphState)
        self.intent_alignment_graph: CompiledStateGraph = IntentAlignmentGraphBuilder().build()

    def build(self) -> CompiledStateGraph:
        self.workflow.add_node("intent_alignment", self.intent_alignment_graph)
        self.workflow.add_node("roll_gate", RollGateNode())
        self.workflow.add_node("action_generator", ActionGeneratorNode())
        self.workflow.add_node("narrator", NarratorNode())

        self.workflow.add_edge(start_key=START, end_key="intent_alignment")
        self.workflow.add_conditional_edges(
            source="intent_alignment",
            path=self._route_to_roll_gate,
            path_map={
                True: "roll_gate",
                False: "action_generator",
            },
        )
        self.workflow.add_edge(start_key="action_generator", end_key="narrator")
        self.workflow.add_edge(start_key="narrator", end_key=END)

        return self.workflow.compile(checkpointer=self._checkpointer)

    def _route_to_roll_gate(self, state: GraphState) -> bool:
        return bool(state.needs_roll)