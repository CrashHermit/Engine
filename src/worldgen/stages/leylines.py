"""Leylines stage: place nexuses, build the web, assign aspects, rasterize.

Pipeline order: ``... → Savagery → Leylines → Biomes``
"""

import random

from src.worldgen.config.worldgen_config import LeylineConfig
from src.worldgen.context import WorldContext
from src.worldgen.features import Lake, LeylineNetwork
from src.worldgen.magic.aspects import assign_aspects
from src.worldgen.magic.fields import rasterize_magic
from src.worldgen.magic.nexus import place_nexuses
from src.worldgen.magic.web import build_web
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.rng import FIELD_MAGIC_FLOOR, FIELD_NEXUS_SCORE, FIELD_VALENCE
from src.worldgen.types import Float64Array


class LeylinesStage:
    """Score + place nexuses, MST + loops, cluster aspects, then rasterize fields.

    Writes ``ctx.leylines`` and the ``magic_strength`` / ``magic_valence`` /
    ``magic_channels`` fields.  Pipeline order: after Savagery, before Biomes.
    """

    def run(self, ctx: WorldContext) -> None:
        """Build the leyline network and write the magic fields."""
        cfg: LeylineConfig = ctx.config.leyline
        geometry = ctx.geometry

        lakes: list[Lake] | None = ctx.lakes
        if lakes is None:
            msg: str = "lakes must be set before LeylinesStage"
            raise RuntimeError(msg)

        # The stage owns the seed; pure functions receive rng / sampled noise.
        rng: random.Random = random.Random(ctx.seed_for("leylines"))

        # --- score noise → nexus placement ---
        score_field: FractalField = FractalField(
            sampler=ctx.noise_for("nexus_score"),
            field_id=FIELD_NEXUS_SCORE,
            octaves=3,
        )
        score_noise: Float64Array = score_field.sample_array(
            xs=geometry.sites[:, 0],
            ys=geometry.sites[:, 1],
            frequency=cfg.score_frequency,
        )

        nexus_cells: list[int] = place_nexuses(
            geometry=geometry,
            fields=ctx.fields,
            lakes=lakes,
            cfg=cfg,
            score_noise=score_noise,
        )

        # --- web: MST + loops ---
        edges: list[tuple[int, int]] = build_web(
            geometry=geometry, nexus_cells=nexus_cells, cfg=cfg
        )

        # --- aspects: clustered valence, mingling channels ---
        valence_field: FractalField = FractalField(
            sampler=ctx.noise_for("valence"),
            field_id=FIELD_VALENCE,
            octaves=2,
        )
        nexus_valence, nexus_channels = assign_aspects(
            geometry=geometry,
            nexus_cells=nexus_cells,
            cfg=cfg,
            valence_noise=valence_field,
            rng=rng,
        )

        network: LeylineNetwork = LeylineNetwork(
            nexus_cells=nexus_cells,
            nexus_valence=nexus_valence,
            nexus_channels=nexus_channels,
            edges=edges,
        )
        ctx.leylines = network

        # --- rasterize per-cell magic fields ---
        floor_field: FractalField = FractalField(
            sampler=ctx.noise_for("magic_floor"),
            field_id=FIELD_MAGIC_FLOOR,
            octaves=3,
        )
        magic_strength, magic_valence, magic_channels = rasterize_magic(
            geometry=geometry,
            network=network,
            cfg=cfg,
            floor_noise=floor_field,
        )

        ctx.fields.magic_strength = magic_strength
        ctx.fields.magic_valence = magic_valence
        ctx.fields.magic_channels = magic_channels
