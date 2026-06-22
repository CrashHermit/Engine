"""Boundary uplift from tectonic plate interactions."""

from collections import deque

import numpy as np

from src.worldgen.config.worldgen_config import PlatesConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_delta
from src.worldgen.noise.field import FractalField
from src.worldgen.types import Float64Array, Int32Array


def _compute_boundary_intensity(
    *, geometry: MeshGeometry, plate_id: Int32Array, drift: Float64Array
) -> tuple[Float64Array, Float64Array]:
    """Return per-cell raw collision and rift intensity on plate borders."""
    n_cells: int = geometry.n_cells
    collision: Float64Array = np.zeros(n_cells, dtype=np.float64)
    rift: Float64Array = np.zeros(n_cells, dtype=np.float64)

    width: float = geometry.width
    height: float = geometry.height
    sites: Float64Array = geometry.sites

    cell_id: int
    for cell_id in range(n_cells):
        plate_i: int = int(plate_id[cell_id])
        drift_i: Float64Array = drift[plate_i]
        site_i: Float64Array = sites[cell_id]

        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor_id: int = int(neighbor_id)
            if plate_id[neighbor_id] == plate_i:
                continue

            plate_j: int = int(plate_id[neighbor_id])
            drift_j: Float64Array = drift[plate_j]
            delta: Float64Array = torus_delta(
                a=site_i, b=sites[neighbor_id], width=width, height=height
            )
            dist: float = float(np.linalg.norm(x=delta))
            if dist == 0.0:
                continue

            direction: Float64Array = delta / dist
            convergence: float = float(np.dot(a=drift_i - drift_j, b=direction))

            if convergence > 0.0:
                collision[cell_id] = max(collision[cell_id], convergence)
            elif convergence < 0.0:
                rift[cell_id] = max(rift[cell_id], -convergence)

    return collision, rift


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


def apply_boundary_uplift(
    *,
    geometry: MeshGeometry,
    plate_id: Int32Array,
    drift: Float64Array,
    uplift: Float64Array,
    config: PlatesConfig,
    belt_noise: FractalField,
    uplift_noise: FractalField,
    frequency: float,
) -> None:
    """Add collision belts and rift seams to ``uplift`` in place."""
    raw_collision, raw_rift = _compute_boundary_intensity(
        geometry=geometry,
        plate_id=plate_id,
        drift=drift,
    )
    smeared_collision: Float64Array = _smear_intensity(
        geometry=geometry,
        raw=raw_collision,
        belt_width=config.belt_width,
        falloff=config.belt_falloff,
    )
    smeared_rift: Float64Array = _smear_intensity(
        geometry=geometry,
        raw=raw_rift,
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
