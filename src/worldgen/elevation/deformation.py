"""Orchestration of motion-driven tectonic relief processes."""

import numpy as np

from src.worldgen.elevation.collision import collision_relief
from src.worldgen.elevation.config import DeformationConfig
from src.worldgen.elevation.divergence import divergence_relief
from src.worldgen.elevation.subduction import subduction_relief
from src.worldgen.elevation.transform import transform_relief
from src.worldgen.geology.boundary_sections import BoundarySections
from src.worldgen.geometry.mesh import Mesh


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
    boundary_shear: np.ndarray,
    arc_variation: np.ndarray,
) -> np.ndarray:
    """Run grouped collision, subduction, divergence, and transform relief."""
    collision = config.collision
    subduction = config.subduction
    divergence = config.divergence
    transform = config.transform
    vertex_count = len(mesh.vertices)
    positive = np.zeros(vertex_count, dtype=np.float64)
    negative = np.zeros(vertex_count, dtype=np.float64)
    if not (
        (collision.width_percent > 0.0 and collision.height_percent != 0.0)
        or (subduction.width_percent > 0.0 and subduction.height_percent != 0.0)
        or (divergence.width_percent > 0.0 and divergence.height_percent != 0.0)
        or (transform.width_percent > 0.0 and transform.height_percent != 0.0)
    ):
        return positive

    lengths = mesh.edge_lengths_percent
    adjacency = mesh.geographic_adjacency
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
    transformed = None
    if transform.width_percent > 0.0 and transform.height_percent != 0.0:
        transformed = transform_relief(
            mesh,
            transform,
            radius_m,
            lengths=lengths,
            adjacency=adjacency,
            crust=crust,
            plate_ids=plate_ids,
            boundary_edge_indices=boundary_edge_indices,
            boundary_sections=boundary_sections,
            boundary_normal=boundary_convergence - boundary_divergence,
            boundary_shear=boundary_shear,
        )
    relief = positive + negative
    if divergent is not None:
        relief += divergent
    if transformed is not None:
        relief += transformed
    return relief
