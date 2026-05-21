from typing import Annotated

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class GraphState(TypedDict):
    message_history: Annotated[list[AnyMessage], add_messages]
    clarity_history: Annotated[list[AnyMessage], add_messages]
    human_message: HumanMessage
    ai_message: AIMessage
