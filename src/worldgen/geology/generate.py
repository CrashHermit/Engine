"""Orchestration of plates, boundaries, and crust generation."""

import numpy as np

from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.boundary import boundary_interactions
from src.worldgen.geology.boundary_sections import generate_boundary_sections
from src.worldgen.geology.config import GeologyConfig
from src.worldgen.geology.crust import generate_crust
from src.worldgen.geology.hotspots import generate_hotspots
from src.worldgen.geology.model import GeologyResult
from src.worldgen.geology.plates import generate_plates
from src.worldgen.geology.volcanism import generate_volcanism


def generate_geology(
    mesh: Mesh,
    config: GeologyConfig,
    *,
    potential_noise_seed: int,
    plate_seed_rng: np.random.Generator,
    plate_motion_rng: np.random.Generator,
    plate_noise_seed: int,
    crust_noise_seed: int,
    crust_rng: np.random.Generator,
    density_noise_seed: int,
    hotspot_rng: np.random.Generator,
    volcanic_rng: np.random.Generator,
    subduction_width_percent: float,
    arc_offset_fraction: float,
    arc_width_fraction: float,
    divergence_width_percent: float,
    axial_width_fraction: float,
    arc_variation: np.ndarray,
) -> GeologyResult:
    """Generate geology and its boundary metadata using independent streams."""
    plates = generate_plates(
        mesh,
        config.plates,
        seed_rng=plate_seed_rng,
        plate_motion_rng=plate_motion_rng,
        noise_seed=plate_noise_seed,
    )
    hotspots = generate_hotspots(
        mesh,
        config.hotspots,
        plates.plate_ids,
        plates.boundary_edge_indices,
        rng=hotspot_rng,
        potential_noise_seed=potential_noise_seed,
    )
    convergence, divergence, shear = boundary_interactions(
        mesh,
        plates.plate_ids,
        plates.plate_rotation,
        plates.boundary_edge_indices,
    )
    crust = generate_crust(
        mesh,
        config.crust,
        noise_seed=crust_noise_seed,
        density_noise_seed=density_noise_seed,
        rng=crust_rng,
    )
    sections = generate_boundary_sections(
        mesh,
        plates.plate_ids,
        crust,
        plates.boundary_edge_indices,
    )
    volcanism = generate_volcanism(
        mesh,
        config.volcanism,
        hotspots=hotspots,
        crust=crust,
        plate_ids=plates.plate_ids,
        boundary_edge_indices=plates.boundary_edge_indices,
        boundary_sections=sections,
        boundary_convergence=convergence,
        boundary_divergence=divergence,
        rng=volcanic_rng,
        subduction_width_percent=subduction_width_percent,
        arc_offset_fraction=arc_offset_fraction,
        arc_width_fraction=arc_width_fraction,
        divergence_width_percent=divergence_width_percent,
        axial_width_fraction=axial_width_fraction,
        arc_variation=arc_variation,
    )
    for array in (convergence, divergence, shear):
        array.setflags(write=False)
    return GeologyResult(
        seed_indices=plates.seed_indices,
        plate_ids=plates.plate_ids,
        plate_rotation=plates.plate_rotation,
        plate_velocity=plates.plate_velocity,
        boundary_edge_indices=plates.boundary_edge_indices,
        boundary_convergence=convergence,
        boundary_divergence=divergence,
        boundary_shear=shear,
        boundary_sections=sections,
        hotspots=hotspots,
        crust=crust,
        volcanism=volcanism,
    )
