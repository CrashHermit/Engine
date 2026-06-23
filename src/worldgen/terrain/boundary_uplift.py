"""Boundary uplift from tectonic plate interactions.

Mountain belts and rift valleys, smeared off the per-cell facts produced once by
``terrain/boundaries.py``.  Collision belts rise on every convergent boundary
(mountains form whether or not the boundary is volcanic); rift valleys carve on
divergent boundaries *except* ocean-ocean spreading, which the vulcanism stage
raises into a mid-ocean ridge instead.
"""

from collections import deque

import numpy as np

from src.worldgen.config.worldgen_config import PlatesConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.noise.field import FractalField
from src.worldgen.terrain.boundaries import BoundaryFacts, BoundaryKind
from src.worldgen.types import BoolArray, Float64Array, Int32Array


def _smear_intensity(
    *, geometry: MeshGeometry, raw: Float64Array, belt_width: int, falloff: float
) -> Float64Array:
    """Multi-source BFS smear with max-combine and per-hop falloff."""
    n_cells: int = geometry.n_cells
    smeared: Float64Array = np.zeros(n_cells, dtype=np.float64)
    queue: deque[tuple[int, float, int]] = deque()

    cell_id: int
    for cell_id in range(n_cells):
        intensity: float = float(raw[cell_id])
        if intensity <= 0.0:
            continue
        smeared[cell_id] = max(smeared[cell_id], intensity)
        queue.append((cell_id, intensity, 0))

    while queue:
        cell_id, intensity, hops = queue.popleft()
        if hops >= belt_width:
            continue

        next_intensity: float = intensity * falloff
        if next_intensity <= 0.0:
            continue

        neighbor_id: int
        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor_id: int = int(neighbor_id)
            if next_intensity <= smeared[neighbor_id]:
                continue
            smeared[neighbor_id] = next_intensity
            queue.append((neighbor_id, next_intensity, hops + 1))

    return smeared


def _sample_site_noise(
    *,
    geometry: MeshGeometry,
    field: FractalField,
    frequency: float,
) -> Float64Array:
    """Sample fractal noise at every mesh site."""
    xs: Float64Array = geometry.sites[:, 0]
    ys: Float64Array = geometry.sites[:, 1]
    return np.fromiter(
        (
            field.sample(x=float(x), y=float(y), frequency=frequency)
            for x, y in zip(xs, ys)
        ),
        dtype=np.float64,
        count=geometry.n_cells,
    )


def _boundary_hop_distance(
    *, geometry: MeshGeometry, plate_id: Int32Array
) -> Int32Array:
    """Per-cell hop distance to the nearest cell that borders another plate.

    Multi-source BFS seeded from every cell with a neighbour on a different
    plate (the plate margins).  Interior cells get their hop count outward.
    """
    n: int = geometry.n_cells
    dist: Int32Array = np.full(n, -1, dtype=np.int32)
    queue: deque[int] = deque()

    cell_id: int
    for cell_id in range(n):
        pid: int = int(plate_id[cell_id])
        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            if int(plate_id[int(neighbor_id)]) != pid:
                dist[cell_id] = 0
                queue.append(cell_id)
                break

    while queue:
        current: int = queue.popleft()
        for neighbor_id in geometry.neighbors_of(cell_id=current):
            nb: int = int(neighbor_id)
            if dist[nb] == -1:
                dist[nb] = dist[current] + 1
                queue.append(nb)

    np.maximum(dist, 0, out=dist)
    return dist


def apply_continental_freeboard(
    *,
    geometry: MeshGeometry,
    plate_id: Int32Array,
    is_continental_cell: BoolArray,
    uplift: Float64Array,
    strength: float,
    reach_frac: float,
) -> None:
    """Raise continental cells into a buoyant platform, in place.

    The edifice ramps from ``0`` at the plate margin to ``strength`` in the deep
    interior over a physical length of ``reach_frac`` of the world span, so the
    lowest continental ground is the coast: rising sea level drowns margins
    first and the continent surfaces as a coherent blob instead of a flat slab
    that floods into ribbons.  Distance is measured in hops but converted to
    physical units, so the ramp is the same shape at any mesh resolution.
    """
    if strength <= 0.0 or reach_frac <= 0.0:
        return

    hops: Int32Array = _boundary_hop_distance(geometry=geometry, plate_id=plate_id)
    spacing: float = float(
        np.sqrt(geometry.width * geometry.height / geometry.n_cells)
    )
    reach: float = reach_frac * max(geometry.width, geometry.height)
    ramp: Float64Array = 1.0 - np.exp(-(hops.astype(np.float64) * spacing) / reach)
    uplift += strength * is_continental_cell.astype(np.float64) * ramp
    np.maximum(uplift, 0.0, out=uplift)


def apply_boundary_uplift(
    *,
    geometry: MeshGeometry,
    facts: BoundaryFacts,
    uplift: Float64Array,
    config: PlatesConfig,
    belt_noise: FractalField,
    uplift_noise: FractalField,
    frequency: float,
) -> None:
    """Add collision belts and (non-oceanic) rift seams to ``uplift`` in place."""
    # Ocean-ocean spreading is left for the vulcanism stage to raise into a
    # mid-ocean ridge; every other divergent boundary carves a rift valley here.
    rift_raw: Float64Array = np.where(
        facts.div_kind == int(BoundaryKind.DIV_OO), 0.0, facts.divergence
    )

    smeared_collision: Float64Array = _smear_intensity(
        geometry=geometry,
        raw=facts.convergence,
        belt_width=config.belt_width,
        falloff=config.belt_falloff,
    )
    smeared_rift: Float64Array = _smear_intensity(
        geometry=geometry,
        raw=rift_raw,
        belt_width=config.belt_width,
        falloff=config.belt_falloff,
    )
    belt_fbm: Float64Array = _sample_site_noise(
        geometry=geometry,
        field=belt_noise,
        frequency=frequency,
    )
    floor_fbm: Float64Array = _sample_site_noise(
        geometry=geometry,
        field=uplift_noise,
        frequency=frequency,
    )
    belt_modulation: Float64Array = 1.0 + config.belt_noise_scale * belt_fbm
    uplift += config.belt_strength * smeared_collision * belt_modulation
    uplift -= config.rift_strength * smeared_rift
    uplift += config.uplift_noise_floor * floor_fbm
    np.maximum(uplift, 0.0, out=uplift)
