"""Subduction trench and volcanic-arc relief propagation."""

import numpy as np

from src.worldgen.elevation.config import SubductionConfig
from src.worldgen.elevation.profiles import subduction_profile
from src.worldgen.field.distance import nearest_source_distances
from src.worldgen.geology.boundary_sections import BoundarySections
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.elevation.sources import boundary_side_sources


def subduction_relief(
    mesh: Mesh,
    config: SubductionConfig,
    radius_m: float,
    *,
    lengths: np.ndarray,
    adjacency: list[list[tuple[int, float]]],
    crust: np.ndarray,
    plate_ids: np.ndarray,
    boundary_edge_indices: np.ndarray,
    boundary_sections: BoundarySections,
    boundary_convergence: np.ndarray,
    arc_variation: np.ndarray,
    positive: np.ndarray,
    negative: np.ndarray,
) -> None:
    """Max/min-combine nearest subduction sources into shared relief envelopes."""
    width = config.width_percent
    if width <= 0.0 or config.height_percent == 0.0:
        return
    source_boundaries = []
    for boundary_index in range(len(boundary_edge_indices)):
        section = int(boundary_sections.edge_section_ids[boundary_index])
        if (
            boundary_convergence[boundary_index] > 0.0
            and int(boundary_sections.subducting_plate_ids[section]) >= 0
        ):
            source_boundaries.append(boundary_index)
    if not source_boundaries:
        return
    source_indices, source_distances, source_ids, region_ids = boundary_side_sources(
        mesh,
        lengths,
        plate_ids,
        crust,
        boundary_edge_indices,
        boundary_sections,
        source_boundaries,
    )
    support = width * max(
        config.trench_width_fraction,
        config.arc_offset_fraction + config.arc_width_fraction,
    )
    distances, winning_ids = nearest_source_distances(
        adjacency,
        source_indices,
        source_distances,
        source_ids,
        region_ids,
        max_distance=support,
    )
    peak_scale = radius_m * config.height_percent / 100.0
    for vertex in range(len(mesh.vertices)):
        source_id = int(winning_ids[vertex])
        if source_id < 0:
            continue
        boundary_index, side = divmod(source_id, 2)
        section = int(boundary_sections.edge_section_ids[boundary_index])
        subducting = int(boundary_sections.subducting_plate_ids[section])
        is_subducting_side = (
            int(boundary_sections.plate_pairs[section, side]) == subducting
        )
        profile = subduction_profile(
            distances[vertex],
            width,
            is_subducting_side,
            trench_width_fraction=config.trench_width_fraction,
            arc_offset_fraction=config.arc_offset_fraction,
            arc_width_fraction=config.arc_width_fraction,
            arc_height_multiplier=config.arc_height_multiplier,
        )
        if not is_subducting_side:
            profile *= float(arc_variation[vertex])
        contribution = (
            peak_scale * float(boundary_convergence[boundary_index]) * profile
        )
        if contribution > 0.0:
            positive[vertex] = max(positive[vertex], contribution)
        elif contribution < 0.0:
            negative[vertex] = min(negative[vertex], contribution)
