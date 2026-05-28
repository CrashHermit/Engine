import operator
from typing import Annotated

from pydantic import BaseModel, Field

from src.core.model.message import Message


class GraphState(BaseModel):
    message_history: Annotated[list[Message], operator.add] = Field(default_factory=list)
    clarity_history: Annotated[list[Message], operator.add] = Field(default_factory=list)
    human_message: Message | None = None
    ai_message: Message | None = None
    question: str | None = None
    is_clarity_achieved: bool | None = None
    location_name: str = ""
    location_description: str = ""
    character_name: str = ""
    character_description: str = ""
