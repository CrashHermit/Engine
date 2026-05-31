from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.core.mechanic.magnitude import Magnitude
from src.node.attribute_selector import AttributeSelectorNode
from src.node.dice_scale import DiceScaleNode
from src.node.final_planner import FinalPlannerNode
from src.node.held_planner import HeldPlannerNode
from src.node.mundane import MundaneNode
from src.node.narrator import NarratorNode
from src.node.resist_offer import ResistOfferNode
from src.node.resist_push_parser import ResistPushParserNode
from src.node.resist_roll import ResistRollNode
from src.node.roll_gate import RollGateNode
from src.node.segmenter import SegmenterNode
from src.node.threat_channel import ThreatChannelNode
from src.node.threat_magnitude import ThreatMagnitudeNode
from src.node.threat_type import ThreatTypeNode
from src.node.turn_close import TurnCloseNode
from src.state import GraphState


def _route_by_roll_gate(state: GraphState) -> str:
    return "segmenter" if state.needs_roll else "mundane"


def _route_by_significance(state: GraphState) -> str:
    m = state.outcome.landed_magnitude if state.outcome else 0
    return "held_planner" if m >= Magnitude.STANDARD else "final_planner"


def _route_after_narrator(state: GraphState) -> str:
    # Held call: scaffold is set but final_planner hasn't run yet.
    if state.held_scaffold is not None and state.final_scaffold is None:
        return "resist_offer"
    return "turn_close"


class ResolutionGraphBuilder:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)

    def build(self) -> CompiledStateGraph:
        narrator = NarratorNode()

        # ── nodes ──────────────────────────────────────────────────────────
        self.workflow.add_node("roll_gate", RollGateNode())
        self.workflow.add_node("mundane", MundaneNode())
        self.workflow.add_node("segmenter", SegmenterNode())

        # Framing fan-out (parallel)
        self.workflow.add_node("attribute_selector", AttributeSelectorNode())
        self.workflow.add_node("threat_type", ThreatTypeNode())
        self.workflow.add_node("threat_magnitude", ThreatMagnitudeNode())
        self.workflow.add_node("threat_channel", ThreatChannelNode())

        self.workflow.add_node("dice_scale", DiceScaleNode())

        # Planner nodes
        self.workflow.add_node("held_planner", HeldPlannerNode())
        self.workflow.add_node("final_planner", FinalPlannerNode())

        # Single narrator instance used at every narration point
        self.workflow.add_node("narrator", narrator)

        self.workflow.add_node("turn_close", TurnCloseNode())

        # Resistance path
        self.workflow.add_node("resist_offer", ResistOfferNode())
        self.workflow.add_node("resist_push_parser", ResistPushParserNode())
        self.workflow.add_node("resist_roll", ResistRollNode())

        # ── edges ──────────────────────────────────────────────────────────
        self.workflow.add_edge(START, "roll_gate")
        self.workflow.add_conditional_edges("roll_gate", _route_by_roll_gate)

        # Mundane path: directive built in code, straight to narrator
        self.workflow.add_edge("mundane", "narrator")

        # Roll path: segmenter → parallel framing fan-out → dice_scale
        self.workflow.add_edge("segmenter", "attribute_selector")
        self.workflow.add_edge("segmenter", "threat_type")
        self.workflow.add_edge("segmenter", "threat_magnitude")
        self.workflow.add_edge("segmenter", "threat_channel")

        self.workflow.add_edge("attribute_selector", "dice_scale")
        self.workflow.add_edge("threat_type", "dice_scale")
        self.workflow.add_edge("threat_magnitude", "dice_scale")
        self.workflow.add_edge("threat_channel", "dice_scale")

        # Significance gate: >= STANDARD → held path; < STANDARD → final path
        self.workflow.add_conditional_edges("dice_scale", _route_by_significance)

        self.workflow.add_edge("held_planner", "narrator")
        self.workflow.add_edge("final_planner", "narrator")

        # After narrator: held call → resist_offer; all other calls → turn_close
        self.workflow.add_conditional_edges("narrator", _route_after_narrator)

        # Resistance path loops back to final_planner
        self.workflow.add_edge("resist_offer", "resist_push_parser")
        self.workflow.add_edge("resist_push_parser", "resist_roll")
        self.workflow.add_edge("resist_roll", "final_planner")

        self.workflow.add_edge("turn_close", END)

        return self.workflow.compile()
