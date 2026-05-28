from typing import Literal

from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["human", "ai", "system", "tool"]
    content: str
    name: str = ""

    def format(self) -> str:
        speaker = self.name if self.name else self.role
        return f"{speaker}: {self.content}"
