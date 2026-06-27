"""Named geographic regions — the gameplay "socket".

Phase 5 (final): a cheap derived pass that segments the mesh into named,
gameplay-addressable :class:`~src.worldgen.features.Region` entities and writes
the per-cell id columns.  Quests, cities, and borders reference regions by id, so
this contract is stable even as the underlying fields churn — re-running simply
re-segments.

Regions are layered, not one partition:

* **Geographic bodies** (``region_id``) — land bodies and ocean bodies; a
  wall-to-wall partition (every cell belongs to exactly one).
* **Biome-regions** (``biome_region_id``) — connected runs of one landscape
  category (forest, plains, ...), *overlapping* the land bodies, on dry land
  only.

All regions share one global id space and ship in a single ``regions`` list, so
gameplay has one lookup; per-tile membership is per-layer (separate id columns).
"""

import numpy as np

from src.core.model.environment.ecology.biome import BiomeEnum
from src.core.model.environment.regions.region import Region, RegionKind
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.regions.landscape import (
    LANDSCAPE_CODE,
    LANDSCAPE_KIND,
    LANDSCAPE_NOUN,
    LANDSCAPE_ORDER,
)
from src.worldgen.types import BoolArray, Float64Array, Int32Array
from src.worldgen.water.lakes import components
from src.worldgen.workspace import Workspace
from src.worldgen.ecology.biomes import derive_centers

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


def _name_suffix(kind: RegionKind) -> str:
    """The trailing landscape noun for a region name ('' / ' Sea' / ' Forest')."""
    if kind == RegionKind.LANDMASS:
        return ""
    if kind == RegionKind.OCEAN:
        return " Sea"
    return f" {LANDSCAPE_NOUN[kind]}"


def _region_name(*, kind: RegionKind, seed: int, region_id: int) -> str:
    """A stable, seed-derived placeholder name with a kind-flavored suffix."""
    rng: np.random.Generator = np.random.default_rng(seed * 1_000_003 + region_id)
    stem: str = _ONSETS[int(rng.integers(len(_ONSETS)))] + _CODAS[
        int(rng.integers(len(_CODAS)))
    ]
    return stem + _name_suffix(kind)


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


def _cell_landscape(
    *,
    dominant_biome: Int32Array,
    biome_mask: BoolArray,
    biome_order: list[BiomeEnum],
) -> Int32Array:
    """Per-cell landscape :class:`RegionKind` value (as int); ``-1`` off the mask."""
    col_to_kind: Int32Array = np.array(
        [LANDSCAPE_CODE[LANDSCAPE_KIND[biome]] for biome in biome_order],
        dtype=np.int32,
    )
    kinds: Int32Array = np.full(dominant_biome.shape[0], -1, dtype=np.int32)
    kinds[biome_mask] = col_to_kind[dominant_biome[biome_mask]]
    return kinds


def assign_regions(
    *,
    geometry: MeshGeometry,
    is_land: BoolArray,
    landmass_id: Int32Array,
    biome_mask: BoolArray,
    dominant_biome: Int32Array,
    biome_order: list[BiomeEnum],
    seed: int,
) -> tuple[Int32Array, Int32Array, list[Region]]:
    """Segment the mesh into named regions across two layers.

    Layer 1 — geographic bodies (``region_id``, wall-to-wall): land cells inherit
    their connected ``landmass_id`` component; ocean cells segment into connected
    bodies.  Layer 2 — biome-regions (``biome_region_id``, dry land only): each
    landscape category's cells segment into connected runs, overlapping layer 1.
    All regions share one global 0-based id space and one ``regions`` list.

    Args:
        geometry: Torus mesh with CSR adjacency.
        is_land: Per-cell land mask (ocean = ~is_land).
        landmass_id: 1-based connected land component per cell (0 = ocean).
        biome_mask: Cells that carry a biome (dry land = is_land & ~is_lake).
        dominant_biome: Per-cell argmax biome column (meaningful where biome_mask).
        biome_order: Column index → ``BiomeEnum`` (from ``derive_centers``).
        seed: World seed, for deterministic region names.

    Returns:
        ``region_id``: Per-cell geographic-body id (0-based; no holes).
        ``biome_region_id``: Per-cell biome-region id (0-based; -1 off dry land).
        ``regions``: All :class:`Region` entities, indexed by their global id.
    """
    n: int = geometry.n_cells
    region_id: Int32Array = np.full(n, -1, dtype=np.int32)
    biome_region_id: Int32Array = np.full(n, -1, dtype=np.int32)
    regions: list[Region] = []
    next_id: int = 0

    def emit(*, members: BoolArray, kind: RegionKind, biome: BiomeEnum | None) -> int:
        """Append one region for ``members`` and return its assigned id."""
        nonlocal next_id
        rid: int = next_id
        regions.append(
            Region(
                id=rid,
                kind=kind,
                name=_region_name(kind=kind, seed=seed, region_id=rid),
                cell_count=int(np.count_nonzero(members)),
                centroid=_torus_centroid(geometry=geometry, members=members),
                dominant_biome=biome,
            )
        )
        next_id += 1
        return rid

    # --- layer 1a: land bodies (reuse the landmass components) ---
    max_landmass: int = int(landmass_id.max()) if landmass_id.size else 0
    for component in range(1, max_landmass + 1):
        members: BoolArray = landmass_id == component
        if not members.any():
            continue
        region_id[members] = emit(
            members=members, kind=RegionKind.LANDMASS, biome=None
        )

    # --- layer 1b: ocean bodies (connected components of the non-land cells) ---
    ocean_labels: Int32Array = components(geometry=geometry, mask=~is_land)
    for component in range(int(ocean_labels.max()) + 1):
        members = ocean_labels == component
        if not members.any():
            continue
        region_id[members] = emit(members=members, kind=RegionKind.OCEAN, biome=None)

    # --- layer 2: biome-regions (connected runs of one landscape category) ---
    cell_kind: Int32Array = _cell_landscape(
        dominant_biome=dominant_biome,
        biome_mask=biome_mask,
        biome_order=biome_order,
    )
    n_biomes: int = len(biome_order)
    for kind in LANDSCAPE_ORDER:
        category_mask: BoolArray = biome_mask & (cell_kind == LANDSCAPE_CODE[kind])
        labels: Int32Array = components(geometry=geometry, mask=category_mask)
        for component in range(int(labels.max()) + 1):
            members = labels == component
            if not members.any():
                continue
            counts: Int32Array = np.bincount(
                dominant_biome[members], minlength=n_biomes
            )
            dominant: BiomeEnum = biome_order[int(counts.argmax())]
            biome_region_id[members] = emit(
                members=members, kind=kind, biome=dominant
            )

    return region_id, biome_region_id, regions


class RegionsStage:
    """Write ``region_id`` / ``biome_region_id`` and the ``Region`` list."""

    reads: tuple[str, ...] = ("biome_weights", "is_lake", "is_land", "landmass_id")
    writes: tuple[str, ...] = ("biome_region_id", "region_id")

    def run(self, ctx: Workspace) -> None:
        """Segment land/ocean bodies and biome-regions into named regions."""
        is_land_field: BoolArray = ctx.fields.is_land

        is_lake_field: BoolArray = ctx.fields.is_lake

        landmass_field: Int32Array = ctx.fields.landmass_id

        weights_field: Float64Array = ctx.fields.biome_weights

        # Biome-regions live on dry land; their landscape is the dominant biome.
        biome_mask: BoolArray = is_land_field & ~is_lake_field
        dominant_biome: Int32Array = np.argmax(weights_field, axis=1).astype(np.int32)
        _center_temp, _center_precip, biome_order = derive_centers()

        region_id, biome_region_id, regions = assign_regions(
            geometry=ctx.geometry,
            is_land=is_land_field,
            landmass_id=landmass_field,
            biome_mask=biome_mask,
            dominant_biome=dominant_biome,
            biome_order=biome_order,
            seed=ctx.config.seed,
        )
        ctx.fields.region_id = region_id
        ctx.fields.biome_region_id = biome_region_id
        ctx.outputs.regions = regions
