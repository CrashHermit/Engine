from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Send

from src.graph.logged_node import LoggedNode
from src.node.attribute_selector import AttributeSelectorNode
from src.node.classify_threat import ClassifyThreatNode
from src.node.dice_scale import DiceScaleNode
from src.node.final_planner import FinalPlannerNode
from src.node.gather_threats import GatherThreatsNode
from src.node.held_planner import HeldPlannerNode
from src.node.mundane import MundaneNode
from src.node.narrator import NarratorNode
from src.node.resist_offer import ResistOfferNode
from src.node.resist_push_parser import ResistPushParserNode
from src.node.resist_roll import ResistRollNode
from src.node.roll_gate import RollGateNode
from src.node.segmenter import SegmenterNode
from src.node.turn_close import TurnCloseNode
from src.state import GraphState


def _route_by_roll_gate(state: GraphState) -> str:
    return "segmenter" if state.needs_roll else "mundane"


def _fan_out_threats(state: GraphState) -> list[Send]:
    """One classify branch per candidate source: every entity present, plus the
    environment. Each Send carries a full GraphState copy with only its own
    source/entity set — LangGraph does NOT coerce a Send payload into the
    pydantic state schema, so passing a dict would hand the branch a bare dict
    (breaking LoggedNode.model_dump and the node's attribute access). model_copy
    keeps the branch typed and preserves the full turn context."""
    sends = [
        Send(
            "classify_threat",
            state.model_copy(update={"classify_source": e.name, "classify_entity": e}),
        )
        for e in state.scene_entities
    ]
    sends.append(
        Send(
            "classify_threat",
            state.model_copy(update={"classify_source": "environment", "classify_entity": None}),
        )
    )
    return sends


def _route_by_significance(state: GraphState) -> str:
    return "held_planner" if state.landed_threats else "final_planner"


def _route_after_narrator(state: GraphState) -> str:
    # Cohesive held setup → begin the resist cycle. Mundane/avoided → close.
    if (
        state.held_scaffold is not None
        and state.final_scaffold is None
        and state.resist_cursor == 0
    ):
        return "resist_offer"
    return "turn_close"


def _route_after_resolution(state: GraphState) -> str:
    # Per-threat resolution line just narrated. Stop on permadeath; otherwise
    # offer the next landed threat, else close.
    if state.character_lost:
        return "turn_close"
    if state.resist_cursor < len(state.resist_queue):
        return "resist_offer"
    return "turn_close"


class ResolutionGraphBuilder:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)

    def build(self) -> CompiledStateGraph:
        self.workflow.add_node("roll_gate", LoggedNode("roll_gate", RollGateNode()))
        self.workflow.add_node("mundane", LoggedNode("mundane", MundaneNode()))
        self.workflow.add_node("segmenter", LoggedNode("segmenter", SegmenterNode()))
        self.workflow.add_node(
            "attribute_selector", LoggedNode("attribute_selector", AttributeSelectorNode())
        )
        self.workflow.add_node("classify_threat", LoggedNode("classify_threat", ClassifyThreatNode()))
        self.workflow.add_node("gather_threats", LoggedNode("gather_threats", GatherThreatsNode()))
        self.workflow.add_node("dice_scale", LoggedNode("dice_scale", DiceScaleNode()))
        self.workflow.add_node("held_planner", LoggedNode("held_planner", HeldPlannerNode()))
        self.workflow.add_node("final_planner", LoggedNode("final_planner", FinalPlannerNode()))
        self.workflow.add_node("narrator", LoggedNode("narrator", NarratorNode()))
        self.workflow.add_node(
            "resolution_narrator", LoggedNode("resolution_narrator", NarratorNode())
        )
        self.workflow.add_node("resist_offer", LoggedNode("resist_offer", ResistOfferNode()))
        self.workflow.add_node(
            "resist_push_parser", LoggedNode("resist_push_parser", ResistPushParserNode())
        )
        self.workflow.add_node("resist_roll", LoggedNode("resist_roll", ResistRollNode()))
        self.workflow.add_node("turn_close", LoggedNode("turn_close", TurnCloseNode()))

        # ── edges ──────────────────────────────────────────────────────────
        self.workflow.add_edge(START, "roll_gate")
        self.workflow.add_conditional_edges("roll_gate", _route_by_roll_gate)
        self.workflow.add_edge("mundane", "narrator")

        # Roll path: segmenter → attribute_selector → per-source fan-out → gather
        self.workflow.add_edge("segmenter", "attribute_selector")
        self.workflow.add_conditional_edges("attribute_selector", _fan_out_threats, ["classify_threat"])
        self.workflow.add_edge("classify_threat", "gather_threats")
        self.workflow.add_edge("gather_threats", "dice_scale")
        self.workflow.add_conditional_edges("dice_scale", _route_by_significance)

        self.workflow.add_edge("held_planner", "narrator")
        self.workflow.add_edge("final_planner", "narrator")
        self.workflow.add_conditional_edges("narrator", _route_after_narrator)

        # Resist cycle: offer → parse → roll → resolution line → loop or close
        self.workflow.add_edge("resist_offer", "resist_push_parser")
        self.workflow.add_edge("resist_push_parser", "resist_roll")
        self.workflow.add_edge("resist_roll", "resolution_narrator")
        self.workflow.add_conditional_edges("resolution_narrator", _route_after_resolution)

        self.workflow.add_edge("turn_close", END)
        return self.workflow.compile()