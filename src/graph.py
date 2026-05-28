from langgraph.graph import END, START, StateGraph

from src.nodes.narrator import NarratorNode
from src.nodes.action_generator import ActionGeneratorNode
from src.nodes.intent_alignment_router import IntentAlignmentRouterNode
from src.nodes.intent_question_generator import IntentQuestionGeneratorNode
from src.nodes.intent_synthesizer import IntentSynthesizerNode
from src.state import GraphState


def build_intent_alignment_subgraph() -> StateGraph:
    workflow: StateGraph = StateGraph(GraphState)

    workflow.add_node("intent_alignment_router", IntentAlignmentRouterNode())
    workflow.add_node("intent_question_generator", IntentQuestionGeneratorNode())
    workflow.add_node("intent_synthesizer", IntentSynthesizerNode())

    workflow.add_edge(START, "intent_alignment_router")
    workflow.add_conditional_edges(
        start_key="intent_alignment_router",
        path="is_clarity_achieved",
        path_map={
            True: "intent_synthesizer",
            False: "intent_question_generator",
        },
    )
    workflow.add_edge("intent_question_generator", END)
    workflow.add_edge("intent_synthesizer", END)

    return workflow.compile()


class Graph:
    def __init__(self) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)

    def build(self) -> StateGraph:
        intent_alignment = build_intent_alignment_subgraph()

        self.workflow.add_node("intent_alignment", intent_alignment)
        self.workflow.add_node("action_generator", ActionGeneratorNode())
        self.workflow.add_node("narrator", NarratorNode())

        self.workflow.add_edge(START, "intent_alignment")
        self.workflow.add_conditional_edges(
            start_key="intent_alignment",
            path="is_clarity_achieved",
            path_map={
                True: "action_generator",
                False: END,
            },
        )
        self.workflow.add_edge("action_generator", "narrator")
        self.workflow.add_edge("narrator", END)

        return self.workflow
