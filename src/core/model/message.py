from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class Message:
    role: Literal["human", "ai", "system", "tool"]
    content: str
    name: str = ""

    def format(self) -> str:
        speaker: str = self.name if self.name else self.role
        return f"{speaker}: {self.content}"
