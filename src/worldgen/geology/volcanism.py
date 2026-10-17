"""Volcanic potential, volcano sites, and episodic activity on a generated mesh."""

from __future__ import annotations


import numpy as np

from src.worldgen.field.distance import nearest_source_distances
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geometry.spherical import angular_distances
from src.worldgen.geology.boundary_sections import BoundarySections
from src.worldgen.geology.model import (
    CrustResult,
    HotspotResult,
    VolcanoSites,
    VolcanismResult,
    VolcanoSource,
    VolcanoState,
)
from src.worldgen.geology.config import VolcanismConfig
from src.worldgen.utilities.curves import smoothstep
from src.worldgen.utilities.sampling import poisson_disk_sample


def _readonly(*arrays: np.ndarray) -> None:
    for array in arrays:
        array.setflags(write=False)


def _footprint(distances: np.ndarray, width: float) -> np.ndarray:
    if width <= 0.0:
        return np.zeros_like(distances)
    return smoothstep(1.0 - distances / width)


def generate_volcanism(
    mesh: Mesh,
    config: VolcanismConfig,
    *,
    hotspots: HotspotResult,
    crust: CrustResult,
    plate_ids: np.ndarray,
    boundary_edge_indices: np.ndarray,
    boundary_sections: BoundarySections,
    boundary_convergence: np.ndarray,
    boundary_divergence: np.ndarray,
    rng: np.random.Generator,
    subduction_width_percent: float,
    arc_offset_fraction: float,
    arc_width_fraction: float,
    divergence_width_percent: float,
    axial_width_fraction: float,
    arc_variation: np.ndarray,
) -> VolcanismResult:
    """Build volcanic fields/sites from precomputed geology without elevation edits.

    Boundary motion arrays are aligned with boundary_edge_indices. Subduction
    arcs spread only across overriding-plate cells, constrained by plate and
    crust region; divergent axes are constrained by plate and crust region.
    """
    cell_count = len(mesh.vertices)
    hotspot_field = np.zeros(cell_count, dtype=np.float64)
    for site, plate, width in zip(
        hotspots.seed_indices, hotspots.plate_ids, hotspots.widths_percent
    ):
        center = mesh.vertices[int(site)]
        distance = angular_distances(
            mesh.vertices, np.broadcast_to(center, mesh.vertices.shape)
        ) * (100.0 / (2.0 * np.pi))
        support = (plate_ids == plate) & (distance < width)
        response = np.zeros(cell_count, dtype=np.float64)
        response[support] = _footprint(distance[support], float(width))
        np.maximum(hotspot_field, response, out=hotspot_field)

    region_ids = plate_ids * 2 + crust.continental_mask
    section_ids = boundary_sections.edge_section_ids
    descending = boundary_sections.subducting_plate_ids[section_ids]
    source_positions = np.flatnonzero((descending >= 0) & (boundary_convergence > 0.0))
    subduction_field = np.zeros(cell_count, dtype=np.float64)
    if len(source_positions) and subduction_width_percent > 0.0:
        edges = mesh.edges[boundary_edge_indices[source_positions]]
        cells = edges.reshape(-1)
        overriding = plate_ids[cells] != np.repeat(descending[source_positions], 2)
        distances, source_ids = nearest_source_distances(
            mesh.geographic_adjacency,
            cells[overriding],
            np.repeat(
                mesh.edge_lengths_percent[boundary_edge_indices[source_positions]]
                * 0.5,
                2,
            )[overriding],
            np.repeat(source_positions, 2)[overriding],
            region_ids,
            max_distance=subduction_width_percent
            * (arc_offset_fraction + arc_width_fraction),
        )
        supported = source_ids >= 0
        positions = distances[supported] / subduction_width_percent
        arc = smoothstep(
            1.0 - np.abs(positions - arc_offset_fraction) / arc_width_fraction
        )
        if arc_offset_fraction > 0.0:
            arc *= smoothstep(positions / arc_offset_fraction)
        subduction_field[supported] = (
            arc * arc_variation[supported] * boundary_convergence[source_ids[supported]]
        )

    source_positions = np.flatnonzero(boundary_divergence > 0.0)
    divergence_field = np.zeros(cell_count, dtype=np.float64)
    width = divergence_width_percent * axial_width_fraction
    if len(source_positions) and width > 0.0:
        edges = mesh.edges[boundary_edge_indices[source_positions]]
        distances, source_ids = nearest_source_distances(
            mesh.geographic_adjacency,
            edges.reshape(-1),
            np.repeat(
                mesh.edge_lengths_percent[boundary_edge_indices[source_positions]]
                * 0.5,
                2,
            ),
            np.repeat(source_positions, 2),
            region_ids,
            max_distance=width,
        )
        supported = source_ids >= 0
        divergence_field[supported] = (
            _footprint(distances[supported], width)
            * boundary_divergence[source_ids[supported]]
        )
        divergence_field[crust.continental_mask] *= hotspots.potential[
            crust.continental_mask
        ]

    potential = np.maximum.reduce((hotspot_field, subduction_field, divergence_field))
    potential = np.maximum(potential, 0.0)
    source_fields = np.stack((hotspot_field, subduction_field, divergence_field))
    source_choice = np.argmax(source_fields, axis=0).astype(np.int8)
    eligible = np.flatnonzero(potential >= config.potential_threshold)
    if config.supplied_site_count and len(eligible):
        sampled = poisson_disk_sample(
            mesh.vertices[eligible],
            config.supplied_site_count,
            config.min_site_distance,
            rng=rng,
            weights=np.maximum(potential[eligible], 1e-12),
        )
        supplied_cells = eligible[sampled]
    else:
        supplied_cells = np.empty(0, dtype=np.int64)

    historic_candidates = np.flatnonzero(potential < config.potential_threshold)
    if config.historical_extinct_site_count and len(historic_candidates):
        sampled = poisson_disk_sample(
            mesh.vertices[historic_candidates],
            config.historical_extinct_site_count,
            config.min_site_distance,
            rng=rng,
        )
        historic_cells = historic_candidates[sampled]
    else:
        historic_cells = np.empty(0, dtype=np.int64)

    supplied_source = source_choice[supplied_cells]
    supplied_strength = potential[supplied_cells].copy()
    persisted = rng.random(len(supplied_cells)) < config.supply_persistence_probability
    eruptions = persisted & (
        rng.random(len(supplied_cells)) < config.eruption_probability
    )
    supplied_strength[~persisted] = 0.0
    supplied_states = np.where(
        eruptions,
        VolcanoState.ERUPTING,
        np.where(persisted, VolcanoState.DORMANT, VolcanoState.EXTINCT),
    ).astype(np.int8)
    intensity = np.where(eruptions, supplied_strength, 0.0)
    historical_source = np.full(
        len(historic_cells), VolcanoSource.HISTORICAL, dtype=np.int8
    )
    historical_states = np.full(
        len(historic_cells), VolcanoState.EXTINCT, dtype=np.int8
    )
    historical_strength = np.zeros(len(historic_cells), dtype=np.float64)
    historical_intensity = np.zeros(len(historic_cells), dtype=np.float64)

    cell_indices = np.concatenate((supplied_cells, historic_cells)).astype(
        np.int64, copy=False
    )
    source_types = np.concatenate((supplied_source, historical_source)).astype(
        np.int8, copy=False
    )
    states = np.concatenate((supplied_states, historical_states)).astype(
        np.int8, copy=False
    )
    supply_strength = np.concatenate((supplied_strength, historical_strength))
    eruption_intensity = np.concatenate((intensity, historical_intensity))
    widths = np.zeros(len(cell_indices), dtype=np.float64)
    heights = np.zeros(len(cell_indices), dtype=np.float64)
    if len(historic_cells):
        widths[len(supplied_cells) :] = rng.uniform(
            config.min_historical_width_percent,
            config.max_historical_width_percent,
            len(historic_cells),
        )
        heights[len(supplied_cells) :] = rng.uniform(
            config.min_historical_height_percent,
            config.max_historical_height_percent,
            len(historic_cells),
        )

    activity = np.zeros(cell_count, dtype=np.float64)
    hotspot_width = float(np.max(hotspots.widths_percent, initial=0.0))
    source_widths = (
        hotspot_width,
        subduction_width_percent * arc_width_fraction,
        divergence_width_percent * axial_width_fraction,
    )
    for cell, source, active, amount in zip(
        supplied_cells, supplied_source, eruptions, intensity
    ):
        if not active:
            continue
        center = mesh.vertices[int(cell)]
        distances = angular_distances(
            mesh.vertices, np.broadcast_to(center, mesh.vertices.shape)
        ) * (100.0 / (2.0 * np.pi))
        field = _footprint(distances, source_widths[int(source)])
        field[plate_ids != plate_ids[cell]] = 0.0
        activity = np.maximum(activity, field * amount)
    volcanic_mask = potential >= config.potential_threshold
    sites = VolcanoSites(
        cell_indices,
        source_types,
        states,
        supply_strength,
        eruption_intensity,
        widths,
        heights,
    )
    _readonly(
        potential,
        activity,
        volcanic_mask,
        hotspot_field,
        subduction_field,
        divergence_field,
        cell_indices,
        source_types,
        states,
        supply_strength,
        eruption_intensity,
        widths,
        heights,
    )
    return VolcanismResult(
        potential,
        activity,
        volcanic_mask,
        sites,
        hotspot_field,
        subduction_field,
        divergence_field,
    )
