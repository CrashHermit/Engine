"""Biome soft weights derived from the one true ``BIOME_GRID``.

Phase 4 step 6.  ``BIOME_GRID`` in ``core/model`` is the single source of
truth: worldgen *derives* each biome's ideal climate point from the band
breakpoints (bands are sevenths; band ``i`` midpoint ``(i + 0.5) / 7``) rather
than maintaining a separate hand-edited centers table.  Soft membership is then
inverse-distance weighting over those centers, done as one ``(n, n_biomes)``
matrix.
"""

from collections import Counter, deque

import numpy as np

from src.core.model.environment.climate.precipitation import (
    ORDER as PRECIP_ORDER,
)
from src.core.model.environment.ecology.biome import BIOME_GRID, BiomeEnum
from src.core.model.environment.shared.temperature import ORDER as TEMP_ORDER
from src.worldgen.config.worldgen_config import BiomeConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import BoolArray, Float64Array, Int32Array


def derive_centers() -> tuple[Float64Array, Float64Array, list[BiomeEnum]]:
    """Return ``(center_temp, center_precip, biome_order)`` from ``BIOME_GRID``.

    Each biome occupies one (temperature band × precipitation band) cell; its
    ideal point is that cell's midpoint.  ``biome_order`` is the single place
    the column index ↔ ``BiomeEnum`` mapping is defined: column
    ``t_idx * n_bands + p_idx``.

    Returns:
        center_temp: Ideal temperature per biome column, shape ``(n_biomes,)``.
        center_precip: Ideal precipitation per biome column.
        biome_order: ``BiomeEnum`` at each column index.
    """
    n_temp: int = len(TEMP_ORDER)
    n_precip: int = len(PRECIP_ORDER)

    center_temp: list[float] = []
    center_precip: list[float] = []
    biome_order: list[BiomeEnum] = []

    t_idx: int
    p_idx: int
    for t_idx, t_band in enumerate(TEMP_ORDER):
        for p_idx, p_band in enumerate(PRECIP_ORDER):
            center_temp.append((t_idx + 0.5) / n_temp)
            center_precip.append((p_idx + 0.5) / n_precip)
            biome_order.append(BIOME_GRID[(t_band, p_band)])

    return (
        np.array(center_temp, dtype=np.float64),
        np.array(center_precip, dtype=np.float64),
        biome_order,
    )


def biome_weights(
    *,
    temperature: Float64Array,
    precipitation: Float64Array,
    is_land: BoolArray,
    center_temp: Float64Array,
    center_precip: Float64Array,
    cfg: BiomeConfig,
) -> Float64Array:
    """Inverse-distance-weighted soft biome membership; shape ``(n, n_biomes)``.

    The broadcast ``T[:, None] - center_temp[None, :]`` *is* the nested
    cell × biome double loop, run in C.  Rows sum to 1 on cells where
    ``is_land`` is True (after the cutoff renormalize) and 0 elsewhere.

    Args:
        temperature: Per-cell warmth in [0, 1].
        precipitation: Per-cell rainfall in [0, 1].
        is_land: Mask of cells that should receive a biome distribution
            (ocean — and lake — cells are zeroed).
        center_temp: Ideal temperature per biome column.
        center_precip: Ideal precipitation per biome column.
        cfg: Biome IDW knobs (``blend_sharpness``, ``weight_cutoff``).

    Returns:
        weights: Soft biome distribution per cell, shape ``(n, n_biomes)``.
    """
    d2: Float64Array = (
        (temperature[:, None] - center_temp[None, :]) ** 2
        + (precipitation[:, None] - center_precip[None, :]) ** 2
    )  # (n, n_biomes)

    weights: Float64Array = 1.0 / (np.sqrt(d2) + 1e-3) ** cfg.blend_sharpness
    weights = weights / weights.sum(axis=1, keepdims=True)

    # Drop negligible weights, then renormalize so rows still sum to 1.
    weights = np.where(weights < cfg.weight_cutoff, 0.0, weights)
    row_sums: Float64Array = weights.sum(axis=1, keepdims=True)
    weights = np.divide(
        weights, row_sums, out=np.zeros_like(weights), where=row_sums > 0.0
    )

    # Ocean / lake cells have no biome.
    weights[~is_land] = 0.0

    return weights


def smooth_biome_weights(
    *,
    geometry: MeshGeometry,
    weights: Float64Array,
    biome_mask: BoolArray,
    cfg: BiomeConfig,
) -> Float64Array:
    """Diffuse the soft biome weights over land neighbours for coherent regions.

    A hard ``argmax`` over the raw weights speckles: wherever climate sits near a
    band boundary, cell-scale wiggle flips the dominant biome, so half the
    "regions" end up a single tile.  Relaxing the soft membership toward the mean
    of its *biome-bearing* neighbours (ocean and lake rows are excluded so coasts
    don't bleed toward zero) turns that speckle into coherent regions with
    gradual ecotones — the real ecological picture — while leaving the
    climate-driven structure intact.  Rows are renormalized to sum to 1 on land.

    Args:
        geometry: Torus mesh with CSR adjacency.
        weights: Soft biome weights, shape ``(n, n_biomes)``.
        biome_mask: Cells that carry a biome (dry land).
        cfg: Biome config (``smoothing_passes``, ``smoothing_strength``).

    Returns:
        The smoothed weights (a new array; the input is not mutated).
    """
    if cfg.smoothing_passes <= 0 or cfg.smoothing_strength <= 0.0:
        return weights

    n: int = geometry.n_cells
    indices: Int32Array = geometry.neighbor_indices
    src: Int32Array = np.repeat(
        np.arange(n, dtype=np.int32), np.diff(geometry.neighbor_offsets)
    )
    maskf: Float64Array = biome_mask.astype(np.float64)
    # Number of biome-bearing neighbours per cell (the masked degree).
    masked_degree: Float64Array = np.bincount(
        src, weights=maskf[indices], minlength=n
    )
    safe: BoolArray = masked_degree > 0.0

    out: Float64Array = weights.copy()
    edge_w: Float64Array = maskf[indices]
    for _ in range(cfg.smoothing_passes):
        neighbor_mean: Float64Array = np.empty_like(out)
        for k in range(out.shape[1]):
            nb_sum: Float64Array = np.bincount(
                src, weights=out[indices, k] * edge_w, minlength=n
            )
            neighbor_mean[:, k] = np.divide(
                nb_sum, masked_degree, out=out[:, k].copy(), where=safe
            )
        out = out + cfg.smoothing_strength * (neighbor_mean - out)
        out[~biome_mask] = 0.0

    row_sums: Float64Array = out.sum(axis=1, keepdims=True)
    out = np.divide(out, row_sums, out=np.zeros_like(out), where=row_sums > 0.0)
    return out


def assign_biome_regions(
    *,
    geometry: MeshGeometry,
    weights: Float64Array,
    biome_mask: BoolArray,
    cfg: BiomeConfig,
) -> Int32Array:
    """Label biome provinces: connected same-biome regions, small ones merged.

    A hard argmax over the soft weights is a patchwork of hundreds of biome
    blobs, many a single cell; real geography reads as a handful of coherent
    regions.  So we (1) take the dominant biome per land cell, (2) flood-fill
    connected same-biome components, and (3) repeatedly absorb any component
    below ``cfg.province_min_fraction`` of land into the neighbouring biome it
    shares the most border with.  A component with no cross-biome land
    neighbour (a small whole island) keeps its biome and stands on its own.

    The soft ``weights`` are read for their argmax only and never mutated — they
    stay the honest per-cell climate truth for fine-grained consumers, while
    ``region_id`` is the coherent regional layer derived from them.

    Args:
        geometry: Torus mesh with CSR adjacency.
        weights: Soft biome weights, shape ``(n, n_biomes)``.
        biome_mask: Cells that carry a biome (dry land).
        cfg: Biome config (``province_min_fraction``).

    Returns:
        ``region_id``: province label per cell (0-based; -1 off the biome mask).
    """
    n: int = geometry.n_cells
    dominant: Int32Array = np.argmax(weights, axis=1).astype(np.int32)
    # ``biome`` is the working per-cell biome the merge mutates; off-mask = -1.
    biome: Int32Array = np.where(biome_mask, dominant, -1).astype(np.int32)

    land_count: int = int(np.count_nonzero(biome_mask))
    min_size: int = max(1, int(cfg.province_min_fraction * land_count))

    # Iterate: relabel components, absorb the small ones, repeat until stable.
    # Absorbing only ever merges components, so the count strictly falls until
    # none below the floor can merge; the ``n`` bound just guards pathology.
    labels: Int32Array
    sizes: list[int]
    _iteration: int
    for _iteration in range(n):
        labels, sizes = _biome_components(
            geometry=geometry, biome=biome, biome_mask=biome_mask
        )
        merged_any: bool = _absorb_small_components(
            geometry=geometry,
            biome=biome,
            labels=labels,
            sizes=sizes,
            min_size=min_size,
        )
        if not merged_any:
            break

    region_id: Int32Array
    region_id, _final = _biome_components(
        geometry=geometry, biome=biome, biome_mask=biome_mask
    )
    return region_id


def _biome_components(
    *,
    geometry: MeshGeometry,
    biome: Int32Array,
    biome_mask: BoolArray,
) -> tuple[Int32Array, list[int]]:
    """Flood-fill connected components of equal ``biome`` over the biome mask.

    Returns ``(labels, sizes)``: a per-cell component id (0-based; -1 off the
    mask) and the cell count of each component, indexed by id.
    """
    n: int = geometry.n_cells
    labels: Int32Array = np.full(shape=n, fill_value=-1, dtype=np.int32)
    sizes: list[int] = []

    cell_id: int
    for cell_id in range(n):
        if not biome_mask[cell_id] or labels[cell_id] >= 0:
            continue
        component_id: int = len(sizes)
        this_biome: int = int(biome[cell_id])
        queue: deque[int] = deque()
        queue.append(cell_id)
        labels[cell_id] = component_id
        size: int = 0
        while queue:
            current: int = queue.popleft()
            size += 1
            neighbor_id: int
            for neighbor_id in geometry.neighbors_of(cell_id=current):
                neighbor: int = int(neighbor_id)
                if (
                    biome_mask[neighbor]
                    and labels[neighbor] < 0
                    and int(biome[neighbor]) == this_biome
                ):
                    labels[neighbor] = component_id
                    queue.append(neighbor)
        sizes.append(size)

    return labels, sizes


def _absorb_small_components(
    *,
    geometry: MeshGeometry,
    biome: Int32Array,
    labels: Int32Array,
    sizes: list[int],
    min_size: int,
) -> bool:
    """Reassign each below-``min_size`` component to its most-bordered neighbour biome.

    Mutates ``biome`` in place.  A component with no differently-labelled land
    neighbour (an isolated small island) is left untouched.  Returns True if any
    component was absorbed.
    """
    n: int = geometry.n_cells
    # Group member cells by component id, smallest first so a tiny patch
    # attaches to a real region instead of seeding a merge chain.
    members: dict[int, list[int]] = {}
    cell_id: int
    for cell_id in range(n):
        component_id: int = int(labels[cell_id])
        if component_id < 0 or sizes[component_id] >= min_size:
            continue
        members.setdefault(component_id, []).append(cell_id)

    merged_any: bool = False
    for component_id in sorted(members, key=lambda c: (sizes[c], c)):
        cells: list[int] = members[component_id]
        # Tally border contact with each neighbouring biome.
        contact: Counter[int] = Counter()
        cell: int
        for cell in cells:
            neighbor_id: int
            for neighbor_id in geometry.neighbors_of(cell_id=cell):
                neighbor: int = int(neighbor_id)
                if int(labels[neighbor]) != component_id and int(biome[neighbor]) >= 0:
                    contact[int(biome[neighbor])] += 1
        if not contact:
            continue  # isolated small island: it is its own province
        # Most border contact wins; ties break by smallest biome id (determinism).
        target_biome: int = min(contact, key=lambda b: (-contact[b], b))
        for cell in cells:
            biome[cell] = target_biome
        merged_any = True

    return merged_any
