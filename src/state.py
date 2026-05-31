import operator
from typing import Annotated

from pydantic import BaseModel, Field

from src.core.model.message import Message


class GraphState(BaseModel):
    message_history: Annotated[list[Message], operator.add] = Field(default_factory=list)
    intent_alignment_history: Annotated[list[Message], operator.add] = Field(default_factory=list)
    human_message: Message | None = None
    ai_message: Message | None = None
    question: str | None = None
    is_intent_alignment_achieved: bool | None = None
    needs_roll: bool | None = None
    lead_up: str | None = None
    contested_beat: str | None = None
    deferred_tail: str | None = None
    action_list: list[str] = Field(default_factory=list)
    location_name: str = ""
    location_description: str = ""
    entities_at_location: list[str] = Field(default_factory=list)
    character_name: str = ""
    character_description: str = ""
