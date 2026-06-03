from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.graph.logged_node import LoggedNode
from src.graph.routers import (
    FRAME_BRANCHES,
    fan_out_ambush,
    fan_out_frame_and_threats,
    route_after_gather,
    route_after_narrator,
    route_after_resolution,
    route_by_roll_gate,
    route_by_significance,
)
from src.node.frame.approach import ApproachNode
from src.node.frame.engagement import EngagementNode
from src.node.frame.mundane import MundaneNode
from src.node.frame.pillar import PillarNode
from src.node.frame.push import PushNode
from src.node.frame.roll_gate import RollGateNode
from src.node.frame.segmenter import SegmenterNode
from src.node.frame.target import TargetNode
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
    """Wires the resolution pipeline as five phase blocks. Each `_add_*` method
    registers its phase's nodes and the edges leaving them; control-flow lives in
    graph/routers.py. The turn flows: frame → (threat → effect) → resolve ⇄ resist."""

    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)

    def build(self) -> CompiledStateGraph:
        self._add_frame()
        self._add_threat()
        self._add_effect()
        self._add_resolve()
        self._add_resist()
        # Turn start: the engagement check sets each creature's posture (aggro +
        # re-engage) before anything else — covers both mundane and roll paths.
        self.workflow.add_edge(START, "engagement")
        return self.workflow.compile()

    def _node(self, name: str, node: object) -> None:
        self.workflow.add_node(name, LoggedNode(name, node))

    def _add_frame(self) -> None:
        """Scope the turn: wake creatures (engagement), gate the roll, and either
        route to mundane narration, the ambush path, or scope the contested beat."""
        self._node("engagement", EngagementNode())
        self._node("roll_gate", RollGateNode())
        self._node("mundane", MundaneNode())
        self._node("segmenter", SegmenterNode())
        # The action read, split into four discrete classifiers that run in
        # parallel (with each other and with the threat enumeration).
        self._node("approach", ApproachNode())
        self._node("pillar", PillarNode())
        self._node("push", PushNode())
        self._node("target", TargetNode())

        self.workflow.add_edge("engagement", "roll_gate")
        self.workflow.add_conditional_edges(
            "roll_gate", route_by_roll_gate, ["segmenter", "ambush", "mundane"]
        )
        self.workflow.add_edge("mundane", "narrator")
        # Segmenter fans out to the four framing classifiers + the threat
        # branches at once. Both arms rejoin at gather_threats — same superstep
        # as the classify branches — so the roll (dice_scale, single-incoming
        # off gather) fires exactly once. Joining framing directly at dice_scale
        # would double-fire it: the framing arm (one hop) and the gather arm
        # (two hops) land in different supersteps, and a LangGraph node re-runs
        # whenever *any* incoming edge updates.
        self.workflow.add_conditional_edges(
            "segmenter",
            fan_out_frame_and_threats,
            [*FRAME_BRANCHES, "classify_threat"],
        )
        for branch in FRAME_BRANCHES:
            self.workflow.add_edge(branch, "gather_threats")

    def _add_threat(self) -> None:
        """Enumerate threats per source (player-action fan-out or world-acts
        ambush), gather them, and scale: by the roll (dice_scale) or full (ambush)."""
        self._node("ambush", AmbushNode())
        self._node("ambush_scale", AmbushScaleNode())
        self._node("classify_threat", ClassifyThreatNode())
        self._node("gather_threats", GatherThreatsNode())
        self._node("dice_scale", DiceScaleNode())

        self.workflow.add_conditional_edges("ambush", fan_out_ambush, ["classify_threat"])
        self.workflow.add_conditional_edges(
            "ambush_scale", route_by_significance, ["held_planner", "final_planner"]
        )
        self.workflow.add_edge("classify_threat", "gather_threats")
        self.workflow.add_conditional_edges(
            "gather_threats", route_after_gather, ["dice_scale", "ambush_scale"]
        )
        self.workflow.add_edge("dice_scale", "apply_effect")

    def _add_effect(self) -> None:
        """The other axis of the same roll: land the player's effect on the target
        (fill the targeted pillar), then decide the held/avoided path."""
        self._node("apply_effect", ApplyEffectNode())
        self.workflow.add_conditional_edges(
            "apply_effect", route_by_significance, ["held_planner", "final_planner"]
        )

    def _add_resolve(self) -> None:
        """Narrate the beat: a cohesive held setup (something landed) or the
        avoided final beat, then route to the resist cycle or close the turn."""
        self._node("held_planner", HeldPlannerNode())
        self._node("final_planner", FinalPlannerNode())
        self._node("narrator", NarratorNode())
        self._node("resolution_narrator", NarratorNode())
        self._node("turn_close", TurnCloseNode())

        self.workflow.add_edge("held_planner", "narrator")
        self.workflow.add_edge("final_planner", "narrator")
        self.workflow.add_conditional_edges(
            "narrator", route_after_narrator, ["resist_offer", "turn_close"]
        )
        self.workflow.add_conditional_edges(
            "resolution_narrator", route_after_resolution, ["resist_offer", "turn_close"]
        )
        self.workflow.add_edge("turn_close", END)

    def _add_resist(self) -> None:
        """Per-threat resist cycle: offer → parse → roll → resolution line, then
        loop to the next landed threat or close (drives resolution_narrator)."""
        self._node("resist_offer", ResistOfferNode())
        self._node("resist_push_parser", ResistPushParserNode())
        self._node("resist_roll", ResistRollNode())

        self.workflow.add_edge("resist_offer", "resist_push_parser")
        self.workflow.add_edge("resist_push_parser", "resist_roll")
        self.workflow.add_edge("resist_roll", "resolution_narrator")