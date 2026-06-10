from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from src.worldgen.context import WorldContext
from src.worldgen.model import CellEnvironment
from src.worldgen.noise.field import FractalField


class ScalarFieldConfig(Protocol):
    """Structural config shared by every smooth scalar-field stage."""

    noise_scale: float
    blend_weight: float
    amplitude: float
    source: str


# ---------------------------------------------------------------------------
# Sources — the "what signal drives the field" seam
# ---------------------------------------------------------------------------


class FieldSource(Protocol):
    """Produces a per-cell base value in ``[0, 1]`` for a scalar field.

    Mirrors ``ElevationProvider``: a source defines *what* signal drives the
    field (noise flavour, latitude band, land mask, composite, ...). Blending
    toward the neutral midpoint, amplitude scaling, and output shaping are all
    applied by ``ScalarFieldStage`` around the source, so a source only has to
    answer "what is the base value at this point?" — already normalised to
    ``[0, 1]``.

    Implementations receive their config and the ``WorldContext`` at
    construction (to build noise fields, precompute masks, etc.).
    """

    def value_at(self, x: float, y: float) -> float:
        """Return the base value in ``[0, 1]`` at world coordinate ``(x, y)``."""
        ...


class FractalFieldSource:
    """Base value from a fractal noise field, normalised to ``[0, 1]``.

    Supports every flavour ``FractalField`` does: ``"fbm"`` (smooth, the
    default), ``"ridged"`` (sharp crests — good for clustered hotspots), and
    ``"billow"`` (rounded lobes).
    """

    def __init__(
        self,
        ctx: WorldContext,
        field_id: int,
        scale: float,
        *,
        octaves: int = 3,
        kind: str = "fbm",
    ) -> None:
        self._field = FractalField(ctx.sampler, field_id, octaves=octaves, kind=kind)
        self._scale = scale
        self._kind = kind

    def value_at(self, x: float, y: float) -> float:
        sample = self._field.sample(x, y, self._scale)
        # Ridged noise already lands in ~[0, 1]; fbm/billow span ~[-1, 1].
        if self._kind == "ridged":
            return max(0.0, min(1.0, sample))
        return (sample + 1.0) * 0.5


# Maps the ``source`` config string to a FractalField flavour. New source
# *kinds* (latitude band, land mask, composite, ...) register in
# ``_build_source`` below — this dict only covers the noise-flavour family.
_FRACTAL_KINDS = {"fractal": "fbm", "ridged": "ridged", "billow": "billow"}


def _build_source(
    config: ScalarFieldConfig, field_id: int, ctx: WorldContext
) -> FieldSource:
    """Select a ``FieldSource`` from config, mirroring ``_build_provider``."""
    kind = _FRACTAL_KINDS.get(config.source)
    if kind is not None:
        return FractalFieldSource(ctx, field_id, config.noise_scale, kind=kind)
    raise ValueError(f"unknown scalar field source: {config.source!r}")


# ---------------------------------------------------------------------------
# Shapers — the "what output curve" seam
# ---------------------------------------------------------------------------

# A shaper turns the blended value in ``[0, 1]`` plus the config amplitude into
# the final stored output. Swapping the shaper is how a field picks its output
# range/curve (unit vs signed today; gamma, terraced, or thresholded later)
# without touching the stage's sampling/iteration/assignment boilerplate.
Shaper = Callable[[float, float], float]


def unit_field(value: float, amplitude: float) -> float:
    """Scale into ``[0, 1]`` (e.g. savagery: 0 = tame, 1 = savage)."""
    return max(0.0, min(1.0, value * amplitude))


def signed_field(value: float, amplitude: float) -> float:
    """Map ``[0, 1]`` onto a signed ``[-1, 1]`` (e.g. alignment)."""
    return max(-1.0, min(1.0, (value * 2.0 - 1.0) * amplitude))


# ---------------------------------------------------------------------------
# Stage
# ---------------------------------------------------------------------------


class ScalarFieldStage:
    """Generates a smooth scalar field on the mesh.

    Shared by savagery and alignment (and any future smooth per-cell scalar).
    For each cell it asks the configured ``FieldSource`` for a base value in
    ``[0, 1]``, blends it toward the neutral midpoint by ``blend_weight``, runs
    it through the ``shape`` curve, and writes the result via ``assign``.
    """

    def __init__(
        self,
        config: ScalarFieldConfig,
        field_id: int,
        *,
        shape: Shaper,
        assign: Callable[[CellEnvironment, float], None],
    ) -> None:
        self._config = config
        self._field_id = field_id
        self._shape = shape
        self._assign = assign

    def run(self, ctx: WorldContext) -> None:
        cfg = self._config
        source = _build_source(cfg, self._field_id, ctx)

        for cell in ctx.data.mesh.cells:
            base = source.value_at(cell.site[0], cell.site[1])
            blended = base * cfg.blend_weight + 0.5 * (1.0 - cfg.blend_weight)
            self._assign(cell.env, self._shape(blended, cfg.amplitude))
