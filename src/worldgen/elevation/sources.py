"""Retained segment-to-geology metadata for continuous tectonic fields."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.worldgen.geometry.boundary import BoundaryNetwork
    from src.worldgen.geology.model import GeologyResult


def boundary_source_rows(
    boundary: BoundaryNetwork, geology: GeologyResult
) -> tuple[np.ndarray, np.ndarray]:
    """Map the supplied plate-boundary order onto retained geology sections."""
    rows_by_edge = {
        int(edge): row for row, edge in enumerate(geology.boundary_edge_indices)
    }
    rows = np.asarray(
        [rows_by_edge[int(edge)] for edge in boundary.edge_indices], dtype=np.int64
    )
    return rows, geology.boundary_sections.edge_section_ids[rows]
