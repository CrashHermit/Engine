from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.graph.logged_node import LoggedNode
from src.graph.routers import (
    fan_out_ambush,
    fan_out_threats,
    route_after_gather,
    route_after_narrator,
    route_after_resolution,
    route_by_roll_gate,
    route_by_significance,
)
from src.node.frame.attribute_selector import AttributeSelectorNode
from src.node.frame.engagement import EngagementNode
from src.node.frame.mundane import MundaneNode
from src.node.frame.roll_gate import RollGateNode
from src.node.frame.segmenter import SegmenterNode
from src.node.threat.ambush import AmbushNode
from src.node.threat.ambush_scale import AmbushScaleNode
from src.node.threat.classify import ClassifyThreatNode
from src.node.threat.dice_scale import DiceScaleNode
from src.node.threat.gather import GatherThreatsNode
from src.node.effect.apply_effect import ApplyEffectNode
from src.node.resolve.final_planner import FinalPlannerNode
from src.node.resolve.held_planner import HeldPlannerNode
from src.node.resolve.narrator import NarratorNode
from src.node.resolve.turn_close import TurnCloseNode
from src.node.resist.offer import ResistOfferNode
from src.node.resist.push_parser import ResistPushParserNode
from src.node.resist.roll import ResistRollNode
from src.state import GraphState


class ResolutionGraphBuilder:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)

    def build(self) -> CompiledStateGraph:
        self.workflow.add_node("engagement", LoggedNode("engagement", EngagementNode()))
        self.workflow.add_node("roll_gate", LoggedNode("roll_gate", RollGateNode()))
        self.workflow.add_node("mundane", LoggedNode("mundane", MundaneNode()))
        self.workflow.add_node("ambush", LoggedNode("ambush", AmbushNode()))
        self.workflow.add_node("ambush_scale", LoggedNode("ambush_scale", AmbushScaleNode()))
        self.workflow.add_node("segmenter", LoggedNode("segmenter", SegmenterNode()))
        self.workflow.add_node(
            "attribute_selector", LoggedNode("attribute_selector", AttributeSelectorNode())
        )
        self.workflow.add_node("classify_threat", LoggedNode("classify_threat", ClassifyThreatNode()))
        self.workflow.add_node("gather_threats", LoggedNode("gather_threats", GatherThreatsNode()))
        self.workflow.add_node("dice_scale", LoggedNode("dice_scale", DiceScaleNode()))
        self.workflow.add_node("apply_effect", LoggedNode("apply_effect", ApplyEffectNode()))
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
        # Turn start: the engagement check sets each creature's posture (aggro +
        # re-engage) before anything else — covers both mundane and roll paths.
        # No-op (no LLM call) when there are no non-hostile creatures.
        self.workflow.add_edge(START, "engagement")
        self.workflow.add_edge("engagement", "roll_gate")
        self.workflow.add_conditional_edges(
            "roll_gate", route_by_roll_gate, ["segmenter", "ambush", "mundane"]
        )
        self.workflow.add_edge("mundane", "narrator")

        # World-acts (ambush) path: hostile creatures strike on a non-contested
        # turn — fan out over them, then land their threats at full magnitude.
        self.workflow.add_conditional_edges("ambush", fan_out_ambush, ["classify_threat"])
        self.workflow.add_conditional_edges("ambush_scale", route_by_significance)

        # Roll path: segmenter → attribute_selector → per-source fan-out → gather
        self.workflow.add_edge("segmenter", "attribute_selector")
        self.workflow.add_conditional_edges("attribute_selector", fan_out_threats, ["classify_threat"])
        self.workflow.add_edge("classify_threat", "gather_threats")
        # Gather fans in for both paths; split on whether the player acted.
        self.workflow.add_conditional_edges(
            "gather_threats", route_after_gather, ["dice_scale", "ambush_scale"]
        )
        # One roll, two axes: scale threats (dice_scale) then land effect on the
        # target (apply_effect) before deciding the held/resist path.
        self.workflow.add_edge("dice_scale", "apply_effect")
        self.workflow.add_conditional_edges("apply_effect", route_by_significance)

        self.workflow.add_edge("held_planner", "narrator")
        self.workflow.add_edge("final_planner", "narrator")
        self.workflow.add_conditional_edges("narrator", route_after_narrator)

        # Resist cycle: offer → parse → roll → resolution line → loop or close
        self.workflow.add_edge("resist_offer", "resist_push_parser")
        self.workflow.add_edge("resist_push_parser", "resist_roll")
        self.workflow.add_edge("resist_roll", "resolution_narrator")
        self.workflow.add_conditional_edges("resolution_narrator", route_after_resolution)

        self.workflow.add_edge("turn_close", END)
        return self.workflow.compile()