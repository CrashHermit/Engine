from typing import Literal

from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["human", "ai", "system", "tool"]
    content: str
    name: str = ""
