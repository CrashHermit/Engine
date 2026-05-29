from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver
from src.nodes.intent_alignment_router import IntentAlignmentRouterNode
from src.nodes.intent_question_generator import IntentQuestionGeneratorNode
from src.nodes.intent_synthesizer import IntentSynthesizerNode
from src.state import 
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.base import BaseCheckpointSaver


class IntentAlignmentGraphBuilder:
    def __init__(self, checkpointer: MemorySaver | None = None) -> None:
        self.workflow: StateGraph = StateGraph(GraphState)

    def build(self) -> CompiledStateGraph:
        self.workflow.add_node("intent_alignment_router", IntentAlignmentRouterNode())
        self.workflow.add_node("intent_question_generator", IntentQuestionGeneratorNode())
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
        self.workflow.add_edge("intent_question_generator", "intent_alignment_router")
        self.workflow.add_edge("intent_synthesizer", END)

        return self.workflow.compile(
            checkpointer=self._checkpointer,
            interrrupt_after=["intent_question_generator"],
        )


def route_by_intent_alignment_router(state: GraphState) -> bool:
    return bool(state.is_intent_alignment_achieved)
