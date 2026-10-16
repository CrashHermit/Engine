"""Generation of coherent tectonic plate-boundary sections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geometry.spherical import angular_distances
from src.worldgen.geometry.topology import boundary_components

if TYPE_CHECKING:
    from src.worldgen.geology.model import CrustResult


@dataclass(frozen=True, slots=True)
class BoundarySections:
    edge_section_ids: np.ndarray
    plate_pairs: np.ndarray
    continental_sides: np.ndarray
    side_effective_density: np.ndarray
    subducting_plate_ids: np.ndarray


def _edge_side_labels(
    mesh: Mesh,
    plate_ids: np.ndarray,
    continental_mask: np.ndarray,
    boundary_edge_indices: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    edges = mesh.edges[boundary_edge_indices]
    pairs = np.sort(plate_ids[edges], axis=1)
    sides = np.empty((len(edges), 2), dtype=bool)
    for index, (left, right) in enumerate(edges):
        left_plate, right_plate = plate_ids[left], plate_ids[right]
        if left_plate == pairs[index, 0]:
            sides[index] = continental_mask[[left, right]]
        else:
            sides[index] = continental_mask[[right, left]]
    return pairs, sides[:, 0], sides[:, 1]


def section_plate_boundaries(
    mesh: Mesh,
    plate_ids: np.ndarray,
    continental_mask: np.ndarray,
    boundary_edge_indices: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Group dual-connected edges by plate pair and ordered crust sides."""
    pairs, left_continental, right_continental = _edge_side_labels(
        mesh, plate_ids, continental_mask, boundary_edge_indices
    )
    labels = np.column_stack((pairs, left_continental, right_continental)).astype(
        np.int64
    )
    edge_section_ids = boundary_components(mesh, boundary_edge_indices, labels)
    section_count = int(edge_section_ids.max()) + 1 if len(edge_section_ids) else 0
    section_pairs = np.empty((section_count, 2), dtype=np.int64)
    section_sides = np.empty((section_count, 2), dtype=bool)
    for section in range(section_count):
        first = int(np.flatnonzero(edge_section_ids == section)[0])
        section_pairs[section] = pairs[first]
        section_sides[section] = (left_continental[first], right_continental[first])
    for array in (edge_section_ids, section_pairs, section_sides):
        array.setflags(write=False)
    return edge_section_ids, section_pairs, section_sides


def _dual_edge_lengths(mesh: Mesh, edge_indices: np.ndarray) -> np.ndarray:
    incidence = mesh.edge_face_indices
    lengths = np.empty(len(edge_indices), dtype=np.float64)
    for position, edge_value in enumerate(edge_indices):
        faces = incidence[int(edge_value)]
        vertices = mesh.dual_vertices[faces]
        lengths[position] = angular_distances(vertices[:1], vertices[1:2])[0]
    return lengths


def generate_boundary_sections(
    mesh: Mesh,
    plate_ids: np.ndarray,
    crust: CrustResult,
    boundary_edge_indices: np.ndarray,
) -> BoundarySections:
    """Generate coherent plate-pair/crust sections and their polarity."""
    edge_section_ids, plate_pairs, continental_sides = section_plate_boundaries(
        mesh,
        plate_ids,
        crust.continental_mask,
        boundary_edge_indices,
    )
    section_count = len(plate_pairs)
    side_density = np.empty((section_count, 2), dtype=np.float64)
    subducting = np.full(section_count, -1, dtype=np.int64)
    edge_lengths = _dual_edge_lengths(mesh, boundary_edge_indices)
    edges = mesh.edges[boundary_edge_indices]
    for section in range(section_count):
        selected = np.flatnonzero(edge_section_ids == section)
        weights = edge_lengths[selected]
        values = np.empty((len(selected), 2), dtype=np.float64)
        for row, edge_position in enumerate(selected):
            left, right = edges[edge_position]
            pair = plate_pairs[section]
            if plate_ids[left] == pair[0]:
                values[row] = crust.region_effective_density[
                    crust.region_ids[[left, right]]
                ]
            else:
                values[row] = crust.region_effective_density[
                    crust.region_ids[[right, left]]
                ]
        side_density[section] = np.average(values, axis=0, weights=weights)
        sides = continental_sides[section]
        if sides.all():
            continue
        if sides[0] != sides[1]:
            oceanic = int(np.flatnonzero(~sides)[0])
            subducting[section] = plate_pairs[section, oceanic]
        elif side_density[section, 0] > side_density[section, 1]:
            subducting[section] = plate_pairs[section, 0]
        elif side_density[section, 1] > side_density[section, 0]:
            subducting[section] = plate_pairs[section, 1]
        else:
            subducting[section] = plate_pairs[section, 0]
    arrays = (
        edge_section_ids,
        plate_pairs,
        continental_sides,
        side_density,
        subducting,
    )
    for array in arrays:
        array.setflags(write=False)
    return BoundarySections(*arrays)
