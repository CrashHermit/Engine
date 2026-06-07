from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.node.intent.alignment_router import IntentAlignmentRouterNode
from src.node.intent.clarification import IntentClarificationNode
from src.node.intent.question_generator import IntentQuestionGeneratorNode
from src.node.intent.synthesizer import IntentSynthesizerNode
from src.state import GraphState


class IntentAlignmentGraphBuilder:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)

    def build(self) -> CompiledStateGraph:
        self.workflow.add_node("intent_alignment_router", IntentAlignmentRouterNode())
        self.workflow.add_node(
            "intent_question_generator", IntentQuestionGeneratorNode()
        )
        self.workflow.add_node("intent_clarification", IntentClarificationNode())
        self.workflow.add_node("intent_synthesizer", IntentSynthesizerNode())

        self.workflow.add_edge(START, "intent_alignment_router")
        self.workflow.add_conditional_edges(
            source="intent_alignment_router",
            path=route_by_intent_alignment_router,
            path_map={
                True: "intent_synthesizer",
                False: "intent_question_generator",
            },
        )
        self.workflow.add_edge("intent_question_generator", "intent_clarification")
        self.workflow.add_edge("intent_clarification", "intent_alignment_router")
        self.workflow.add_edge("intent_synthesizer", END)
        return self.workflow.compile()


def route_by_intent_alignment_router(state: GraphState) -> bool:
    return bool(state.get("is_intent_alignment_achieved"))
