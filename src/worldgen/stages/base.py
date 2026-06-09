from __future__ import annotations

from typing import Protocol

from src.worldgen.context import WorldContext


class Stage(Protocol):
    """Common interface for all worldgen pipeline stages.

    Every stage receives a ``WorldContext``, mutates ``ctx.data`` in place,
    and returns the same context so stages can be chained in a simple loop.
    """

    def run(self, ctx: WorldContext) -> WorldContext:
        """Execute the stage and return the (potentially modified) context."""
        ...
