"""Named geographic regions — the gameplay "socket".

Phase 4 (final): a cheap derived pass that segments the mesh into named,
gameplay-addressable :class:`~src.worldgen.features.Region` entities and writes a
per-cell ``region_id``.  Quests, cities, and borders reference regions by id, so
this contract is stable even as the underlying fields churn — re-running simply
re-segments.

The socket ships the two geography-stable kinds (land bodies, ocean bodies),
which together form a wall-to-wall partition: every cell belongs to exactly one
region.  Ecology- and weather-derived kinds (forests, plains, marine biomes)
layer on later without changing the contract.
"""

import numpy as np

from src.worldgen.features import Region, RegionKind
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import BoolArray, Float64Array, Int32Array
from src.worldgen.water.lakes import components

# Deterministic placeholder namer.  Real procedural naming (language-aware,
# kind-flavored) is a follow-up; this gives every region a stable, seed-derived
# label so the socket is genuinely "named" and swappable at one call site.
_ONSETS: tuple[str, ...] = (
    "Vor", "Kel", "Mar", "Tar", "Sel", "Dun", "Ash", "Bryn", "Cor", "Fen",
    "Gal", "Hal", "Ith", "Jor", "Lor", "Mor", "Nor", "Oss", "Pyr", "Quel",
    "Ral", "Syl", "Thal", "Ull", "Vael", "Wyn", "Xan", "Yrl", "Zel", "Aen",
)
_CODAS: tuple[str, ...] = (
    "ath", "mor", "wyn", "dar", "eth", "holt", "mere", "fell", "gard", "heim",
    "mar", "reach", "stead", "vale", "wick", "crest", "run", "shol", "tide", "ness",
)


def _region_name(*, kind: RegionKind, seed: int, region_id: int) -> str:
    """A stable, seed-derived placeholder name; oceans get a sea-suffix."""
    rng: np.random.Generator = np.random.default_rng(seed * 1_000_003 + region_id)
    stem: str = _ONSETS[int(rng.integers(len(_ONSETS)))] + _CODAS[
        int(rng.integers(len(_CODAS)))
    ]
    if kind == RegionKind.OCEAN:
        return f"{stem} Sea"
    return stem


def _torus_centroid(
    *, geometry: MeshGeometry, members: BoolArray
) -> tuple[float, float]:
    """Centroid of a member set on the torus, via per-axis circular mean.

    A plain mean is wrong across the wraparound seam (a body straddling x=0 would
    centroid to the middle of the map).  Average each coordinate as an angle and
    map back, so wrapping bodies center correctly.
    """
    sites: Float64Array = geometry.sites[members]
    if sites.shape[0] == 0:
        return (0.0, 0.0)

    def circular(values: Float64Array, span: float) -> float:
        angles: Float64Array = values / span * (2.0 * np.pi)
        mean_angle: float = float(
            np.arctan2(np.sin(angles).mean(), np.cos(angles).mean())
        )
        return float((mean_angle % (2.0 * np.pi)) / (2.0 * np.pi) * span)

    return (
        circular(sites[:, 0], geometry.width),
        circular(sites[:, 1], geometry.height),
    )


def assign_regions(
    *,
    geometry: MeshGeometry,
    is_land: BoolArray,
    landmass_id: Int32Array,
    seed: int,
) -> tuple[Int32Array, list[Region]]:
    """Partition the mesh into named regions; return ``(region_id, regions)``.

    Land cells inherit their connected ``landmass_id`` component (one
    :class:`RegionKind.LANDMASS` region each); ocean cells are segmented into
    connected components (one :class:`RegionKind.OCEAN` region each).  Together
    these cover every cell, so ``region_id`` has no ``-1`` holes.  Region ids are
    global and 0-based, matching the per-cell ``region_id`` and the baked
    ``grid.region_id``.

    Args:
        geometry: Torus mesh with CSR adjacency.
        is_land: Per-cell land mask (ocean = ~is_land).
        landmass_id: 1-based connected land component per cell (0 = ocean).
        seed: World seed, for deterministic region names.

    Returns:
        ``region_id``: Per-cell global region id (0-based; no holes).
        ``regions``: The :class:`Region` entities, indexed by id.
    """
    n: int = geometry.n_cells
    region_id: Int32Array = np.full(n, -1, dtype=np.int32)
    regions: list[Region] = []
    next_id: int = 0

    # --- land bodies: reuse the landmass components ---
    max_landmass: int = int(landmass_id.max()) if landmass_id.size else 0
    for component in range(1, max_landmass + 1):
        members: BoolArray = landmass_id == component
        count: int = int(np.count_nonzero(members))
        if count == 0:
            continue
        region_id[members] = next_id
        regions.append(
            Region(
                id=next_id,
                kind=RegionKind.LANDMASS,
                name=_region_name(
                    kind=RegionKind.LANDMASS, seed=seed, region_id=next_id
                ),
                cell_count=count,
                centroid=_torus_centroid(geometry=geometry, members=members),
            )
        )
        next_id += 1

    # --- ocean bodies: connected components of the non-land cells ---
    ocean_labels: Int32Array = components(geometry=geometry, mask=~is_land)
    max_ocean: int = int(ocean_labels.max()) if ocean_labels.size else -1
    for component in range(max_ocean + 1):
        members = ocean_labels == component
        count = int(np.count_nonzero(members))
        if count == 0:
            continue
        region_id[members] = next_id
        regions.append(
            Region(
                id=next_id,
                kind=RegionKind.OCEAN,
                name=_region_name(
                    kind=RegionKind.OCEAN, seed=seed, region_id=next_id
                ),
                cell_count=count,
                centroid=_torus_centroid(geometry=geometry, members=members),
            )
        )
        next_id += 1

    return region_id, regions
