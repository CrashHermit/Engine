from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.graph.intent_alignment_graph import IntentAlignmentGraphBuilder
from src.graph.resolution_graph import ResolutionGraphBuilder
from src.state import GraphState


class MainGraphBuilder:
    def __init__(self, *, checkpointer: BaseCheckpointSaver) -> None:
        self._checkpointer: BaseCheckpointSaver = checkpointer
        self.workflow: StateGraph = StateGraph(GraphState)
        # Subgraphs compile without their own checkpointer; they inherit the
        # parent's at runtime, which is what makes any internal interrupt()
        # pause and resume the whole main graph.
        self.intent_alignment_graph: CompiledStateGraph = IntentAlignmentGraphBuilder().build()
        self.resolution_graph: CompiledStateGraph = ResolutionGraphBuilder().build()

    def build(self) -> CompiledStateGraph:
        self.workflow.add_node("intent_alignment", self.intent_alignment_graph)
        self.workflow.add_node("resolution", self.resolution_graph)

        self.workflow.add_edge(START, "intent_alignment")
        self.workflow.add_edge("intent_alignment", "resolution")
        self.workflow.add_edge("resolution", END)

        return self.workflow.compile(checkpointer=self._checkpointer)