"""Plausibility-band assertions: catch *implausible* (not just contradictory) output.

The invariant suites prove the world is internally consistent (ranges, rivers
reach the sea, determinism).  These bands catch the regressions that look like a
valid world but aren't a *believable* one: 50 volcanoes, an all-cold-desert
biome mix, a pinned or runaway land fraction.  Bands are deliberately wide — they
flag gross regressions, not taste.

Runs at a mid-high mesh so hydrology forms; a few representative (preset, seed)
worlds rather than the full matrix, to stay quick.
"""

from dataclasses import replace

import numpy as np
import pytest

from src.worldgen.config import presets as P
from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.pipeline import WorldgenPipeline

# Mesh big enough that drainage networks form (below ~6k cells rivers fragment
# into a resolution artifact); kept under the 12k default so the suite is quick.
PLAUSIBLE_CELLS: int = 8000
PLAUSIBLE_SIZE: int = 100

# Representative worlds: a balanced continent world, a supercontinent, and an
# ocean world (whose short rivers are legitimate — see the river check).
CASES: list[tuple[str, int]] = [
    ("earthlike", 1),
    ("earthlike", 42),
    ("pangaea", 42),
    ("archipelago", 1),
]

_CACHE: dict[tuple[str, int], tuple] = {}


def _world(preset: str, seed: int):
    key = (preset, seed)
    if key not in _CACHE:
        base: WorldgenConfig = getattr(P, preset)()
        cfg = replace(base, mesh=MeshConfig(cell_count=PLAUSIBLE_CELLS))
        _CACHE[key] = WorldgenPipeline(cfg).run_debug(seed=seed, size=PLAUSIBLE_SIZE)
    return _CACHE[key]


def _dominant_land_biomes(world) -> tuple[int, float]:
    """Return (distinct dominant biomes, max single-biome share) over dry land."""
    g = world.grid
    land = g.is_land & ~g.is_lake
    dominant = np.argmax(g.biome_weights[land], axis=1)
    counts = np.bincount(dominant)
    total = int(counts.sum()) or 1
    return int(np.count_nonzero(counts)), float(counts.max() / total)


@pytest.mark.parametrize(("preset", "seed"), CASES)
def test_land_fraction_in_clamp(preset: str, seed: int) -> None:
    """Land fraction is emergent but stays inside the configured guardrails."""
    world, _ctx = _world(preset, seed)
    lo, hi = world.config.sea_level.land_fraction_clamp
    frac = float(np.mean(world.grid.is_land))
    assert lo - 1e-6 <= frac <= hi + 1e-6, f"land fraction {frac:.3f} outside [{lo}, {hi}]"


@pytest.mark.parametrize(("preset", "seed"), CASES)
def test_volcano_count_iconic(preset: str, seed: int) -> None:
    """Discrete volcanoes sit at iconic landmark scale, not a scatter of dozens."""
    world, _ctx = _world(preset, seed)
    n = len(world.volcanoes)
    assert 3 <= n <= 25, f"volcano count {n} outside iconic band [3, 25]"


@pytest.mark.parametrize(("preset", "seed"), CASES)
def test_caldera_minority(preset: str, seed: int) -> None:
    """Calderas are a minority of volcanoes (a crater lake is the exception)."""
    world, _ctx = _world(preset, seed)
    n = len(world.volcanoes)
    calderas = sum(1 for v in world.volcanoes if v.has_caldera)
    assert calderas <= max(4, n // 2), f"{calderas} calderas of {n} volcanoes"


@pytest.mark.parametrize(("preset", "seed"), CASES)
def test_biome_diversity(preset: str, seed: int) -> None:
    """The biome mix is varied: several biomes present, none swallowing the map."""
    world, _ctx = _world(preset, seed)
    distinct, max_share = _dominant_land_biomes(world)
    assert distinct >= 6, f"only {distinct} distinct land biomes (want >= 6)"
    assert max_share <= 0.45, f"one biome covers {max_share:.0%} of land (want <= 45%)"


@pytest.mark.parametrize(("preset", "seed"), CASES)
def test_temperate_not_frozen(preset: str, seed: int) -> None:
    """Cold land (the two coldest of seven temperature bands) is not the majority."""
    world, _ctx = _world(preset, seed)
    g = world.grid
    land = g.is_land & ~g.is_lake
    cold_fraction = float((g.temperature[land] < 2.0 / 7.0).mean())
    assert cold_fraction < 0.55, f"cold land fraction {cold_fraction:.2f} (want < 0.55)"


@pytest.mark.parametrize(("preset", "seed"), CASES)
def test_rivers_present_and_long_enough(preset: str, seed: int) -> None:
    """Real river networks form.

    On a world with a major landmass, the longest river spans a meaningful part
    of it.  Ocean worlds (no major landmass) legitimately have only short island
    streams, so the length floor is waived there.
    """
    world, _ctx = _world(preset, seed)
    assert len(world.rivers) > 0, "no rivers at all"
    longest = max(len(r.cells) for r in world.rivers)

    has_major = any(lm.landmass_class >= 3 for lm in world.landmasses)
    if has_major:
        assert longest >= 10, f"longest river {longest} cells on a major landmass"
