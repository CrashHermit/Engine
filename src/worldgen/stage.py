"""The pipeline ``Stage`` protocol and its declared data dependencies.

A stage is thin wiring: it reads config + fields from the workspace, calls the
pure algorithm(s) co-located in its domain module, and writes results back.
Stages are co-located with their algorithm (``terrain/erosion.py`` exports both
``erode`` and ``ErosionStage``); the pipeline lists them in order.

Each stage declares the field names it ``reads`` and ``writes`` so the pipeline can
validate data dependencies at startup (see ``pipeline._validate_stage_deps``):
every required read must be produced by an earlier stage (or the stage itself).
``reads_optional`` lists fields a stage reads at their *zero-initialized* state on
purpose (a deliberate forward reference), exempt from that check.
"""

from typing import Protocol

from src.worldgen.workspace import Workspace


class Stage(Protocol):
    """Pipeline stage that mutates ``ctx.fields`` (and workspace scratch/outputs)."""

    reads: tuple[str, ...]  #: Field names this stage consumes.
    writes: tuple[str, ...]  #: Field names this stage produces.
    reads_optional: tuple[str, ...]  #: Fields read at zero-init on purpose (forward refs).

    def run(self, ctx: Workspace) -> None:
        """Execute the stage."""
        ...
