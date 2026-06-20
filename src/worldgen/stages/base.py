from typing import Protocol

from src.worldgen.context import WorldContext


class Stage(Protocol):
    """Pipeline stage that mutates ctx.fields in place."""

    def run(self, ctx: WorldContext) -> None:
        """Execute the stage."""
        ...
