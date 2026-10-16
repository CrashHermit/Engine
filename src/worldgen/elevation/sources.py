"""Boundary-side source arrays shared by tectonic relief processes."""

import numpy as np

from src.worldgen.geology.boundary_sections import BoundarySections
from src.worldgen.geometry.mesh import Mesh


def boundary_side_sources(
    mesh: Mesh,
    lengths: np.ndarray,
    plate_ids: np.ndarray,
    crust: np.ndarray,
    boundary_edge_indices: np.ndarray,
    boundary_sections: BoundarySections,
    boundary_indices: list[int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build parallel source vertex, initial-distance, and source-ID arrays."""
    region_ids = 2 * plate_ids + crust.astype(np.int64)
    source_indices = []
    source_distances = []
    source_ids = []
    for boundary_index in boundary_indices:
        section = int(boundary_sections.edge_section_ids[boundary_index])
        edge = int(boundary_edge_indices[boundary_index])
        initial = float(lengths[edge]) * 0.5
        for side in range(2):
            plate = int(boundary_sections.plate_pairs[section, side])
            source_id = boundary_index * 2 + side
            region = 2 * plate + int(boundary_sections.continental_sides[section, side])
            for vertex_value in mesh.edges[edge]:
                vertex = int(vertex_value)
                if region_ids[vertex] != region:
                    continue
                source_indices.append(vertex)
                source_distances.append(initial)
                source_ids.append(source_id)
    return (
        np.asarray(source_indices, dtype=np.int64),
        np.asarray(source_distances, dtype=np.float64),
        np.asarray(source_ids, dtype=np.int64),
        region_ids,
    )
