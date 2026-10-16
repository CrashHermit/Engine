"""Intraplate hotspot placement from potential-weighted candidate cells."""

import numpy as np

from src.worldgen.field.distance import multi_source_distances
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.config import HotspotConfig
from src.worldgen.geology.model import HotspotResult
from src.worldgen.utilities.sampling import poisson_disk_sample

from src.worldgen.field.noise import normalized_noise


def generate_hotspots(
    mesh: Mesh,
    config: HotspotConfig,
    plate_ids: np.ndarray,
    boundary_edge_indices: np.ndarray,
    *,
    rng: np.random.Generator,
    potential_noise_seed: int,
) -> HotspotResult:
    """Place spaced intraplate hotspots, biasing placement toward potential."""
    potential = normalized_noise(
        mesh.vertices, config.potential, seed=potential_noise_seed
    )
    if config.count == 0:
        seed_indices = np.empty(0, dtype=np.int64)
        selected_plate_ids = np.empty(0, dtype=np.int64)
        widths = np.empty(0, dtype=np.float64)
        heights = np.empty(0, dtype=np.float64)
        for array in (seed_indices, selected_plate_ids, widths, heights):
            array.setflags(write=False)
        return HotspotResult(
            seed_indices, selected_plate_ids, widths, heights, potential
        )

    lengths = mesh.edge_lengths_percent
    boundary_edges = mesh.edges[boundary_edge_indices]
    source_indices = boundary_edges.reshape(-1)
    source_distances = np.repeat(lengths[boundary_edge_indices] * 0.5, 2)
    boundary_distances = multi_source_distances(
        mesh,
        source_indices,
        source_distances,
        lengths,
        plate_ids,
        adjacency=mesh.geographic_adjacency,
    )
    candidate_indices = np.flatnonzero(
        boundary_distances >= config.boundary_clearance_percent
    )
    weights = 1.0 + config.potential_bias * potential[candidate_indices]
    selected_positions = poisson_disk_sample(
        mesh.vertices[candidate_indices],
        config.count,
        config.min_seed_distance,
        rng=rng,
        weights=weights,
    )
    seed_indices = candidate_indices[selected_positions]
    selected_plate_ids = plate_ids[seed_indices].copy()
    widths = rng.uniform(
        config.min_width_percent, config.max_width_percent, len(seed_indices)
    )
    heights = rng.uniform(
        config.min_height_percent, config.max_height_percent, len(seed_indices)
    )
    for array in (seed_indices, selected_plate_ids, widths, heights):
        array.setflags(write=False)
    return HotspotResult(seed_indices, selected_plate_ids, widths, heights, potential)
