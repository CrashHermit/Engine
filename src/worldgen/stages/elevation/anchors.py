from __future__ import annotations

import math
import random

from src.worldgen.config.worldgen_config import AnchorConfig, ElevationConfig
from src.worldgen.context import WorldContext
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.sampler import FIELD_ANCHOR_ISLAND


def _toroidal_distance(
    ax: float,
    ay: float,
    bx: float,
    by: float,
    width: float,
    height: float,
) -> float:
    """Minimum distance between two points on a torus."""
    dx = abs(ax - bx) % width
    dx = min(dx, width - dx)
    dy = abs(ay - by) % height
    dy = min(dy, height - dy)
    return math.hypot(dx, dy)


def _place_anchors(
    count: int,
    min_spacing: float,
    width: float,
    height: float,
    rng: random.Random,
) -> list[tuple[float, float]]:
    """Place ``count`` anchor points with minimum toroidal spacing."""
    anchors: list[tuple[float, float]] = []
    max_attempts = count * 200
    for _ in range(max_attempts):
        if len(anchors) >= count:
            break
        x = rng.uniform(0.0, width)
        y = rng.uniform(0.0, height)
        if all(
            _toroidal_distance(x, y, ax, ay, width, height) >= min_spacing
            for ax, ay in anchors
        ):
            anchors.append((x, y))
    while len(anchors) < count:
        anchors.append((rng.uniform(0.0, width), rng.uniform(0.0, height)))
    return anchors


def _smooth_falloff(distance: float, radius: float) -> float:
    """Smooth cosine falloff from 1 at centre to 0 at ``radius``."""
    t = min(1.0, distance / radius)
    return (math.cos(t * math.pi) + 1.0) * 0.5


class ContinentAnchorProvider:
    """Elevation provider that places continents at explicit seed points.

    Generates ``num_continents`` anchor locations with minimum toroidal
    spacing, builds a radial-falloff mask for each, and adds a separate
    island pass for smaller land masses scattered through the ocean.

    Coastlines are made organic by the shared domain warp applied in
    ``ElevationStage`` before ``elevation_at`` is queried, so this provider
    contains no warp logic of its own.

    Gives direct control over:
    * how many continents there are (``num_continents``)
    * their spread and minimum separation (``min_continent_spacing``)
    * their size (``continent_radius``)
    * how many fringe islands appear (``island_count``, ``island_radius``)
    """

    def __init__(
        self,
        elev_config: ElevationConfig,
        anchor_config: AnchorConfig,
        ctx: WorldContext,
    ) -> None:
        cfg = anchor_config
        mesh = ctx.data.mesh
        assert mesh is not None

        self._width = mesh.width
        self._height = mesh.height
        self._island_weight = cfg.island_weight
        self._island_field = FractalField(ctx.sampler, FIELD_ANCHOR_ISLAND, octaves=3)

        span = min(self._width, self._height)
        self._continent_radius = cfg.continent_radius * span
        self._island_radius = cfg.island_radius * span

        self._continent_anchors = _place_anchors(
            cfg.num_continents,
            cfg.min_continent_spacing * span,
            self._width,
            self._height,
            ctx.rng,
        )
        self._island_anchors = _place_anchors(
            cfg.island_count,
            self._island_radius * 1.5,
            self._width,
            self._height,
            ctx.rng,
        )

    def elevation_at(self, x: float, y: float) -> float:
        continent_val = max(
            _smooth_falloff(
                _toroidal_distance(x, y, ax, ay, self._width, self._height),
                self._continent_radius,
            )
            for ax, ay in self._continent_anchors
        )
        island_val = max(
            _smooth_falloff(
                _toroidal_distance(x, y, ax, ay, self._width, self._height),
                self._island_radius,
            )
            for ax, ay in self._island_anchors
        ) * self._island_weight

        organic = self._island_field.sample(x, y, 1.5) * 0.15
        return continent_val + island_val + organic
