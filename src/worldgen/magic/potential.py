"""The ley potential: magic's 'elevation', which mana flows down.

Phase 4 step 1.  Magic is generated like water, so it needs a potential to flow
over.  That potential has two parts:

* the **ley-mantle** — a low-frequency field that is magic's own deep geography
  (rock-independent), broad enough to be a climate baseline.  Its highs are
  wellsprings (sources), its lows are drains (sinks).
* the rock **bones** — fault stress and ridge lines, fine and linear, carved as
  *troughs* into the potential so the flow branches dendritically along the
  world's fractures (a smooth ley-mantle alone would give a few broad flows).

``combined_potential = ley_mantle − bones_weight · bones``.
"""

import numpy as np

from src.worldgen.config.worldgen_config import MagicConfig
from src.worldgen.geometry.field_ops import diffuse
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.noise.field import FractalField
from src.worldgen.terrain.boundaries import BoundaryFacts
from src.worldgen.types import Float64Array


def build_ley_mantle(
    *,
    geometry: MeshGeometry,
    mantle_noise: FractalField,
    cfg: MagicConfig,
) -> Float64Array:
    """Low-frequency FBm 'ley-mantle' over the mesh, in roughly [-1, 1].

    Args:
        geometry: Torus mesh providing site positions.
        mantle_noise: FBm field sampled at each cell site.
        cfg: Magic configuration (ley-mantle frequency).

    Returns:
        ley_mantle: Per-cell ley-mantle value (the broad magic baseline).
    """
    return mantle_noise.sample_array(
        xs=geometry.sites[:, 0],
        ys=geometry.sites[:, 1],
        frequency=cfg.ley_mantle_frequency,
    )


def build_structural_bones(
    *,
    geometry: MeshGeometry,
    facts: BoundaryFacts,
    slope: Float64Array,
    cfg: MagicConfig,
) -> Float64Array:
    """Fine, linear rock structure in [0, 1]: fault stress + ridge lines.

    Fault stress is the boundary convergence + divergence; ridges are the
    high-slope cells.  Both are max-normalized, weighted, summed, lightly
    smoothed, and re-normalized so the result is a clean [0, 1] trough mask.

    Args:
        geometry: Torus mesh with CSR adjacency (for smoothing).
        facts: Per-cell boundary facts (convergence + divergence).
        slope: Per-cell steepest-descent gradient.
        cfg: Magic configuration (bones weights, ridge percentile, smoothing).

    Returns:
        bones: Per-cell structural intensity in [0, 1].
    """
    # --- fault stress: convergence + divergence, max-normalized ---
    fault: Float64Array = facts.convergence + facts.divergence
    fault_max: float = float(fault.max())
    fault_norm: Float64Array = (
        fault / fault_max if fault_max > 0.0 else np.zeros_like(fault)
    )

    # --- ridges: slope over a high percentile, clipped ---
    slope_ref: float = float(np.percentile(a=slope, q=cfg.bones_ridge_percentile))
    ridge: Float64Array = (
        np.clip(slope / slope_ref, 0.0, 1.0)
        if slope_ref > 0.0
        else np.zeros_like(slope)
    )

    bones: Float64Array = (
        cfg.bones_boundary_weight * fault_norm + cfg.bones_ridge_weight * ridge
    )

    bones = diffuse(
        geometry=geometry,
        field=bones,
        strength=cfg.bones_smoothing_strength,
        passes=cfg.bones_smoothing,
    )

    bones_max: float = float(bones.max())
    return bones / bones_max if bones_max > 0.0 else bones


def combine_potential(
    *,
    ley_mantle: Float64Array,
    bones: Float64Array,
    cfg: MagicConfig,
) -> Float64Array:
    """Combine the ley-mantle baseline and the bones troughs into one potential.

    ``combined = ley_mantle − bones_weight · bones`` — the bones carve troughs the
    mana flow concentrates into.

    Args:
        ley_mantle: Broad low-frequency magic baseline (roughly [-1, 1]).
        bones: Fine structural trough mask in [0, 1].
        cfg: Magic configuration (bones coupling weight).

    Returns:
        combined_potential: Per-cell ley potential (mana's 'elevation').
    """
    return ley_mantle - cfg.bones_weight * bones
