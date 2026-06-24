"""World census: a one-paragraph summary of a generated world.

The regression eyeball — run it over presets and seeds to confirm nothing
crashed and the numbers look like a world (land fraction near target, rivers
and lakes present, a connected leyline web, a plausible biome mix).

    uv run python scripts/census.py
    uv run python -m cProfile -s cumtime scripts/census.py | head -30
"""

import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Imports after sys.path setup so `src` resolves when run as a script.
# ruff: noqa: E402
from src.worldgen.config.presets import PRESETS
from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.ecology.biomes import derive_centers
from src.worldgen.features import WorldData
from src.worldgen.pipeline import WorldgenPipeline

# Census mesh is smaller than the 12k default so the sweep stays quick.  Keep
# it high enough that drainage actually forms, though: below ~6k cells the
# hydrology is too coarse and rivers read as stubs (a resolution artifact, not
# the real network — at the 12k production mesh the same seeds carry
# continent-spanning rivers).  Exact river *lengths* remain resolution-sensitive
# here; the continent-spanning guarantee is a full-resolution plausibility test.
CENSUS_CELLS: int = 6000
CENSUS_SIZE: int = 96
CENSUS_SEEDS: tuple[int, ...] = (1, 7, 42)


def census(world: WorldData) -> str:
    """Return a one-line census paragraph for a generated world."""
    grid = world.grid
    is_land = grid.is_land
    land_fraction: float = float(np.mean(is_land))

    class_names: dict[int, str] = {1: "island", 2: "landmass", 3: "major"}
    class_counts: Counter[int] = Counter(lm.landmass_class for lm in world.landmasses)
    landmass_summary: str = ", ".join(
        f"{class_counts[c]} {class_names[c]}" for c in (3, 2, 1) if class_counts[c]
    ) or "none"

    longest_river: int = max((len(r.cells) for r in world.rivers), default=0)
    terminal_lakes: int = sum(1 for lk in world.lakes if lk.outlet_cell is None)
    calderas: int = sum(1 for v in world.volcanoes if v.has_caldera)

    # Ocean-current eyeball: how far ocean SST departs from its *latitude-band*
    # mean (the radiative baseline currents perturb).  Warm currents sit above
    # their band, cold currents below; near-zero spread means currents do
    # nothing.  Uses only grid latitude + sst (insolation is mesh-side only).
    ocean = ~is_land
    warm_anom: float = 0.0
    cold_anom: float = 0.0
    if ocean.any():
        lat_band = np.floor(np.abs(grid.latitude[ocean]) * 16).astype(int)
        sst_ocean = grid.sst[ocean]
        band_mean = np.zeros_like(sst_ocean)
        for b in np.unique(lat_band):
            sel = lat_band == b
            band_mean[sel] = sst_ocean[sel].mean()
        anom = sst_ocean - band_mean
        warm_anom = float(anom.max())
        cold_anom = float(anom.min())

    # Dominant-biome histogram over dry-land tiles.
    _ct, _cp, biome_order = derive_centers()
    land_tiles = is_land & ~grid.is_lake
    dominant = np.argmax(grid.biome_weights[land_tiles], axis=1)
    biome_counts: Counter[int] = Counter(int(c) for c in dominant)
    total_land: int = int(np.count_nonzero(land_tiles)) or 1
    top5: str = ", ".join(
        f"{biome_order[col].value} {100 * n / total_land:.0f}%"
        for col, n in biome_counts.most_common(5)
    )

    return (
        f"seed {world.seed}: {100 * land_fraction:.0f}% land across "
        f"{len(world.landmasses)} landmasses ({landmass_summary}); "
        f"{len(world.rivers)} rivers (longest {longest_river} cells), "
        f"{len(world.lakes)} lakes ({terminal_lakes} terminal); "
        f"{len(world.volcanoes)} volcanoes ({calderas} calderas); "
        f"{len(world.nexuses)} nexuses, "
        f"{len(world.veins)} veins; "
        f"currents +{warm_anom:.2f}/{cold_anom:.2f} SST. "
        f"Top biomes: {top5}."
    )


def main() -> None:
    """Print a census for every preset across the census seeds."""
    name: str
    base: WorldgenConfig
    for name, base in PRESETS.items():
        cfg: WorldgenConfig = replace(base, mesh=MeshConfig(cell_count=CENSUS_CELLS))
        print(f"== {name} ==")
        seed: int
        for seed in CENSUS_SEEDS:
            world: WorldData = WorldgenPipeline(cfg).run(seed=seed, size=CENSUS_SIZE)
            print("  " + census(world))


if __name__ == "__main__":
    main()
