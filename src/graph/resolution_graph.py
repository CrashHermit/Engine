from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.node.attribute_selector import AttributeSelectorNode
from src.node.dice_scale import DiceScaleNode
from src.node.held_planner import HeldPlannerNode
from src.node.narrator import NarratorNode
from src.node.resist_offer import ResistOfferNode
from src.node.resist_push_parser import ResistPushParserNode
from src.node.resist_roll import ResistRollNode
from src.node.roll_gate import RollGateNode
from src.node.segmenter import SegmenterNode
from src.node.threat_channel import ThreatChannelNode
from src.node.threat_magnitude import ThreatMagnitudeNode
from src.node.threat_type import ThreatTypeNode
from src.state import GraphState


def _route_by_roll_gate(state: GraphState) -> str:
    return "segmenter" if state.needs_roll else "narrator"


def _route_by_outcome(state: GraphState) -> str:
    if state.outcome is not None and state.outcome.landed_magnitude > 0:
        return "held_planner"
    return "narrator"


def _route_after_narrator(state: GraphState) -> str:
    # If the held_scaffold is set the narrator just wrote held prose; offer resistance.
    if state.held_scaffold is not None:
        return "resist_offer"
    return END


class ResolutionGraphBuilder:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)

    def build(self) -> CompiledStateGraph:
        # ── nodes ──────────────────────────────────────────────────────────
        self.workflow.add_node("roll_gate", RollGateNode())
        self.workflow.add_node("segmenter", SegmenterNode())

        # Framing fan-out (parallel)
        self.workflow.add_node("attribute_selector", AttributeSelectorNode())
        self.workflow.add_node("threat_type", ThreatTypeNode())
        self.workflow.add_node("threat_magnitude", ThreatMagnitudeNode())
        self.workflow.add_node("threat_channel", ThreatChannelNode())

        self.workflow.add_node("dice_scale", DiceScaleNode())

        # Consequence path
        self.workflow.add_node("held_planner", HeldPlannerNode())
        self.workflow.add_node("narrator", NarratorNode())
        self.workflow.add_node("resist_offer", ResistOfferNode())
        self.workflow.add_node("resist_push_parser", ResistPushParserNode())
        self.workflow.add_node("resist_roll", ResistRollNode())
        self.workflow.add_node("narrator_final", NarratorNode())

        # ── edges ──────────────────────────────────────────────────────────
        self.workflow.add_edge(START, "roll_gate")

        # Gate: no roll → narrator direct; roll → segmenter
        self.workflow.add_conditional_edges("roll_gate", _route_by_roll_gate)

        # Framing fan-out: segmenter feeds four parallel classifiers
        self.workflow.add_edge("segmenter", "attribute_selector")
        self.workflow.add_edge("segmenter", "threat_type")
        self.workflow.add_edge("segmenter", "threat_magnitude")
        self.workflow.add_edge("segmenter", "threat_channel")

        # All four join at dice_scale
        self.workflow.add_edge("attribute_selector", "dice_scale")
        self.workflow.add_edge("threat_type", "dice_scale")
        self.workflow.add_edge("threat_magnitude", "dice_scale")
        self.workflow.add_edge("threat_channel", "dice_scale")

        # Outcome routing: avoided/zero → narrator; consequence landed → held_planner
        self.workflow.add_conditional_edges("dice_scale", _route_by_outcome)

        # Consequence path
        self.workflow.add_edge("held_planner", "narrator")

        # After narrator: if held_scaffold set → resist_offer; else → END
        self.workflow.add_conditional_edges("narrator", _route_after_narrator)

        self.workflow.add_edge("resist_offer", "resist_push_parser")
        self.workflow.add_edge("resist_push_parser", "resist_roll")
        self.workflow.add_edge("resist_roll", "narrator_final")
        self.workflow.add_edge("narrator_final", END)

        return self.workflow.compile()
