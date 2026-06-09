from __future__ import annotations

"""Scan multiple seeds and print a landmass-size histogram for each.

Usage::

    uv run python scripts/scan_seeds.py --seeds 0 1 42 100 200 --size 80
    uv run python scripts/scan_seeds.py --count 20 --size 80
    uv run python scripts/scan_seeds.py --preset archipelago --count 5

This makes it easy to hunt for seeds that produce desired continent distributions
without launching the full graphical viewer.
"""

import argparse
import random
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ruff: noqa: E402
from src.worldgen.config.presets import PRESETS
from src.worldgen.config.worldgen_config import WorldgenConfig
from src.worldgen.data import WorldData
from src.worldgen.pipeline import WorldgenPipeline


def _run_seed(seed: int, size: int, config: WorldgenConfig) -> None:
    from dataclasses import replace

    cfg = replace(config)
    world = WorldgenPipeline(cfg).run(WorldData(size=size, seed=seed))

    sizes = world.landmass_sizes
    total_land = sum(sizes.values())
    if total_land == 0:
        print(f"  seed {seed:>6}: no land")
        return

    sorted_sizes = sorted(sizes.values(), reverse=True)
    fractions = [s / total_land for s in sorted_sizes]
    num_major = sum(1 for f in fractions if f >= 0.10)
    num_medium = sum(1 for f in fractions if 0.02 <= f < 0.10)
    num_small = sum(1 for f in fractions if f < 0.02)

    bars = "".join(
        ("M" if f >= 0.10 else ("m" if f >= 0.02 else ".")) for f in fractions[:20]
    )
    grid_land_pct = (
        100
        * sum(1 for t in world.grid if t.position.is_land)
        // len(world.grid)
    )
    print(
        f"  seed {seed:>6}: {len(sizes):>3} components  "
        f"major={num_major} mid={num_medium} small={num_small}  "
        f"land={grid_land_pct}%  [{bars}]"
    )
    top3 = "  ".join(f"{f:.1%}" for f in fractions[:3])
    print(f"           top3: {top3}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan seeds and print landmass histograms."
    )
    parser.add_argument("--seeds", type=int, nargs="+", help="Explicit seed list")
    parser.add_argument(
        "--count", type=int, default=10, help="Number of random seeds (default 10)"
    )
    parser.add_argument("--size", type=int, default=80, help="Grid size (default 80)")
    parser.add_argument(
        "--preset",
        choices=list(PRESETS),
        default=None,
        help="Named world preset",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seeds: list[int] = args.seeds or [
        random.randint(0, 2**31 - 1) for _ in range(args.count)
    ]
    config = PRESETS[args.preset] if args.preset else WorldgenConfig()

    preset_label = args.preset or "default"
    print(f"Scanning {len(seeds)} seeds  size={args.size}  preset={preset_label}")
    print("  Key: M=major (>=10%)  m=medium (2-10%)  .=small (<2%)\n")

    for seed in seeds:
        _run_seed(seed, args.size, config)

    print("\nDone.")


if __name__ == "__main__":
    main()
