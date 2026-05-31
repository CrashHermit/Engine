from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.node.attribute_selector import AttributeSelectorNode
from src.node.dice_scale import DiceScaleNode
from src.node.narrator import NarratorNode
from src.node.roll_gate import RollGateNode
from src.node.segmenter import SegmenterNode
from src.node.threat_channel import ThreatChannelNode
from src.node.threat_magnitude import ThreatMagnitudeNode
from src.node.threat_type import ThreatTypeNode
from src.state import GraphState


def route_by_roll_gate(state: GraphState) -> str:
    return "segmenter" if state.needs_roll else "narrator"


class ResolutionGraphBuilder:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)

    def build(self) -> CompiledStateGraph:
        self.workflow.add_node("roll_gate", RollGateNode())
        self.workflow.add_node("segmenter", SegmenterNode())
        self.workflow.add_node("attribute_selector", AttributeSelectorNode())
        self.workflow.add_node("threat_type", ThreatTypeNode())
        self.workflow.add_node("threat_magnitude", ThreatMagnitudeNode())
        self.workflow.add_node("threat_channel", ThreatChannelNode())
        self.workflow.add_node("narrator", NarratorNode())
        self.workflow.add_node("dice_scale", DiceScaleNode())
        self.workflow.add_edge(START, "roll_gate")

        self.workflow.add_conditional_edges("roll_gate", route_by_roll_gate)
        self.workflow.add_edge("segmenter", "attribute_selector")
        self.workflow.add_edge("segmenter", "threat_type")
        self.workflow.add_edge("segmenter", "threat_magnitude")
        self.workflow.add_edge("segmenter", "threat_channel")
        self.workflow.add_edge("attribute_selector", "dice_scale")
        self.workflow.add_edge("threat_type", "dice_scale")
        self.workflow.add_edge("threat_magnitude", "dice_scale")
        self.workflow.add_edge("threat_channel", "dice_scale")
        self.workflow.add_edge("dice_scale", "narrator")
        self.workflow.add_edge("narrator", END)

        return self.workflow.compile()


def route_by_intent_alignment_router(state: GraphState) -> bool:
    return bool(state.is_intent_alignment_achieved)
