from __future__ import annotations

from typing import Protocol

from src.worldgen.context import WorldContext


class Stage(Protocol):
    """Common interface for all worldgen pipeline stages.

    Every stage receives a ``WorldContext`` and mutates ``ctx.data`` in place.
    """

    def run(self, ctx: WorldContext) -> None:
        """Execute the stage, mutating ``ctx.data`` in place."""
        ...
