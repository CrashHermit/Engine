from pydantic import BaseModel

from core.model.message import Message


class GraphState(BaseModel):
    human_message: Message | None = None
    ai_message: Message | None = None
