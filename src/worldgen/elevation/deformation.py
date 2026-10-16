"""Orchestration of motion-driven tectonic relief processes."""

import numpy as np

from src.worldgen.elevation.collision import collision_relief
from src.worldgen.elevation.config import DeformationConfig
from src.worldgen.elevation.divergence import divergence_relief
from src.worldgen.elevation.subduction import subduction_relief
from src.worldgen.field.distance import weighted_adjacency
from src.worldgen.geology.boundary_sections import BoundarySections
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geometry.spherical import edge_lengths_percent


def tectonic_relief(
    mesh: Mesh,
    config: DeformationConfig,
    radius_m: float,
    *,
    crust: np.ndarray,
    plate_ids: np.ndarray,
    boundary_edge_indices: np.ndarray,
    boundary_sections: BoundarySections,
    boundary_convergence: np.ndarray,
    boundary_divergence: np.ndarray,
    arc_variation: np.ndarray,
) -> np.ndarray:
    """Run grouped collision, subduction, and divergence relief processes."""
    collision = config.collision
    subduction = config.subduction
    divergence = config.divergence
    vertex_count = len(mesh.vertices)
    positive = np.zeros(vertex_count, dtype=np.float64)
    negative = np.zeros(vertex_count, dtype=np.float64)
    if not (
        (collision.width_percent > 0.0 and collision.height_percent != 0.0)
        or (subduction.width_percent > 0.0 and subduction.height_percent != 0.0)
        or (divergence.width_percent > 0.0 and divergence.height_percent != 0.0)
    ):
        return positive

    lengths = edge_lengths_percent(mesh)
    adjacency = weighted_adjacency(mesh, lengths)
    divergent = divergence_relief(
        mesh,
        divergence,
        radius_m,
        lengths=lengths,
        adjacency=adjacency,
        crust=crust,
        plate_ids=plate_ids,
        boundary_edge_indices=boundary_edge_indices,
        boundary_sections=boundary_sections,
        boundary_divergence=boundary_divergence,
    )
    subduction_relief(
        mesh,
        subduction,
        radius_m,
        lengths=lengths,
        adjacency=adjacency,
        crust=crust,
        plate_ids=plate_ids,
        boundary_edge_indices=boundary_edge_indices,
        boundary_sections=boundary_sections,
        boundary_convergence=boundary_convergence,
        arc_variation=arc_variation,
        positive=positive,
        negative=negative,
    )
    collision_relief(
        mesh,
        collision,
        radius_m,
        lengths=lengths,
        adjacency=adjacency,
        crust=crust,
        plate_ids=plate_ids,
        boundary_edge_indices=boundary_edge_indices,
        boundary_sections=boundary_sections,
        boundary_convergence=boundary_convergence,
        positive=positive,
    )
    if divergent is None:
        return positive + negative
    return positive + negative + divergent
