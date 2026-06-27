"""Magic stage: mana hydrology — ley potential, accumulation, veins, nexuses.

Magic is generated like water (see ``docs/worldgen-magic-redesign-plan.md``):
a low-frequency ley-mantle field, perturbed into troughs by the rock 'bones',
forms a ``combined_potential``; a source emission flows down it and accumulates
into dendritic veins exactly as discharge accumulates into rivers.  Channels
(corpus/mens/anima) ride the flow and mix at confluences; nexus poles are the
potential's extrema; mana-current fields are the flow's direction and speed.

Pipeline order: ``... → Savagery → Magic → Biomes``
"""

import numpy as np

from src.worldgen.config.worldgen_config import MagicConfig
from src.worldgen.workspace import Workspace
from src.core.model.environment.magic.nexus import Nexus
from src.core.model.environment.magic.vein import Vein
from src.worldgen.magic.accumulate import (
    accumulate_strength,
    compute_source_emission,
    normalize_strength,
)
from src.worldgen.magic.channels import mix_channels, seed_source_channels
from src.worldgen.magic.flow import compute_magic_flow
from src.worldgen.magic.nexuses import extract_nexuses
from src.worldgen.magic.potential import (
    build_ley_mantle,
    build_structural_bones,
    combine_potential,
)
from src.worldgen.magic.veins import classify_veins, extract_veins
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.rng import (
    FIELD_CHANNEL_ANIMA,
    FIELD_CHANNEL_CORPUS,
    FIELD_CHANNEL_MENS,
    FIELD_LEY_MANTLE,
)
from src.worldgen.terrain.boundaries import BoundaryFacts
from src.worldgen.terrain.routing import compute_receivers, priority_flood
from src.worldgen.types import BoolArray, Float64Array, Int32Array


class MagicStage:
    """Build the ley potential, accumulate mana, extract veins/nexuses, flow.

    Writes ``magic_strength`` / ``magic_channels`` / ``magic_flow_*`` /
    ``is_vein`` / ``vein_id`` / ``is_nexus`` / ``nexus_id`` and the
    ``ctx.outputs.veins`` / ``ctx.outputs.nexuses`` feature lists.
    """

    reads: tuple[str, ...] = ("slope",)
    writes: tuple[str, ...] = ("is_nexus", "is_vein", "magic_channels", "magic_flow_speed", "magic_flow_u", "magic_flow_v", "magic_strength", "nexus_id", "vein_id")

    def run(self, ctx: Workspace) -> None:
        """Generate the mana hydrology and write all magic fields + features."""
        cfg: MagicConfig = ctx.config.magic
        geometry = ctx.geometry
        n: int = geometry.n_cells

        facts: BoundaryFacts | None = ctx.scratch.boundary_facts
        if facts is None:
            msg: str = "boundary_facts must be set before MagicStage"
            raise RuntimeError(msg)

        slope_field: Float64Array | None = ctx.fields.slope
        if slope_field is None:
            msg = "slope must be set before MagicStage"
            raise RuntimeError(msg)
        slope: Float64Array = slope_field

        # --- 1. ley potential: ley-mantle baseline minus rock-bone troughs ---
        mantle_noise: FractalField = FractalField(
            sampler=ctx.noise_for("ley_mantle"),
            field_id=FIELD_LEY_MANTLE,
            octaves=cfg.ley_mantle_octaves,
        )
        ley_mantle: Float64Array = build_ley_mantle(
            geometry=geometry, mantle_noise=mantle_noise, cfg=cfg
        )
        bones: Float64Array = build_structural_bones(
            geometry=geometry, facts=facts, slope=slope, cfg=cfg
        )
        combined_potential: Float64Array = combine_potential(
            ley_mantle=ley_mantle, bones=bones, cfg=cfg
        )

        # --- 2. route over the potential (base = lowest-potential sinks) ---
        n_base: int = max(1, int(cfg.base_fraction * n))
        base_cells: Int32Array = np.argpartition(a=combined_potential, kth=n_base)[
            :n_base
        ].astype(np.int32)
        potential_routed: Float64Array = priority_flood(
            geometry=geometry, z=combined_potential, base_cells=base_cells
        )
        receiver: Int32Array = compute_receivers(
            geometry=geometry, z_route=potential_routed
        )

        # --- 3. emission → accumulation → log-normalized strength ---
        source_emission: Float64Array = compute_source_emission(
            ley_mantle=ley_mantle, cfg=cfg
        )
        accum: Float64Array = accumulate_strength(
            receiver=receiver,
            potential_routed=potential_routed,
            source_emission=source_emission,
        )
        magic_strength: Float64Array = normalize_strength(accum=accum)

        # --- 4. channels: seed source flavor, mix downstream ---
        source_channels: Float64Array = seed_source_channels(
            xs=geometry.sites[:, 0],
            ys=geometry.sites[:, 1],
            corpus_noise=FractalField(
                sampler=ctx.noise_for("channel_corpus"),
                field_id=FIELD_CHANNEL_CORPUS,
                octaves=2,
            ),
            mens_noise=FractalField(
                sampler=ctx.noise_for("channel_mens"),
                field_id=FIELD_CHANNEL_MENS,
                octaves=2,
            ),
            anima_noise=FractalField(
                sampler=ctx.noise_for("channel_anima"),
                field_id=FIELD_CHANNEL_ANIMA,
                octaves=2,
            ),
            frequency=cfg.channel_frequency,
        )
        magic_channels: Float64Array = mix_channels(
            receiver=receiver,
            potential_routed=potential_routed,
            source_emission=source_emission,
            source_channels=source_channels,
            accum=accum,
            magic_strength=magic_strength,
        )

        # --- 5. nexuses (poles) then veins (paths reference pole ids) ---
        nexuses: list[Nexus]
        nexus_id: Int32Array
        is_nexus: BoolArray
        nexuses, nexus_id, is_nexus = extract_nexuses(
            geometry=geometry,
            combined_potential=combined_potential,
            source_channels=source_channels,
            cfg=cfg,
        )

        is_vein: BoolArray = classify_veins(magic_strength=magic_strength, cfg=cfg)
        veins: list[Vein]
        vein_id: Int32Array
        veins, vein_id = extract_veins(
            geometry=geometry,
            receiver=receiver,
            magic_strength=magic_strength,
            channels=magic_channels,
            potential_routed=potential_routed,
            is_vein=is_vein,
            nexus_id=nexus_id,
        )

        # --- 6. mana currents ---
        magic_flow_u, magic_flow_v, magic_flow_speed = compute_magic_flow(
            geometry=geometry,
            receiver=receiver,
            combined_potential=combined_potential,
            magic_strength=magic_strength,
            cfg=cfg,
        )

        # --- write fields + features ---
        ctx.fields.magic_strength = magic_strength
        ctx.fields.magic_channels = magic_channels
        ctx.fields.magic_flow_u = magic_flow_u
        ctx.fields.magic_flow_v = magic_flow_v
        ctx.fields.magic_flow_speed = magic_flow_speed
        ctx.fields.is_vein = is_vein
        ctx.fields.vein_id = vein_id
        ctx.fields.is_nexus = is_nexus
        ctx.fields.nexus_id = nexus_id
        ctx.outputs.veins = veins
        ctx.outputs.nexuses = nexuses
        ctx.scratch.magic_potential = combined_potential
