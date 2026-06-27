"""The pipeline ``Stage`` protocol.

A stage is thin wiring: it reads config + fields from the context, calls the pure
algorithm(s) co-located in its domain module, and writes results back.  Stages are
co-located with their algorithm (``terrain/erosion.py`` exports both ``erode`` and
``ErosionStage``); the pipeline lists them in order.
"""

from typing import Protocol

from src.worldgen.context import WorldContext


class Stage(Protocol):
    """Pipeline stage that mutates ``ctx.fields`` (and context scratch) in place."""

    def run(self, ctx: WorldContext) -> None:
        """Execute the stage."""
        ...
