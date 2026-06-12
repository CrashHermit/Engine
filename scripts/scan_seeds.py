from __future__ import annotations

"""Scan multiple seeds and print placeholder-elevation land fractions.

Usage::

    uv run python scripts/scan_seeds.py --seeds 0 1 42 100 200 --size 80
    uv run python scripts/scan_seeds.py --count 20 --size 80
    uv run python scripts/scan_seeds.py --preset archipelago --count 5
"""

import argparse
import random
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ruff: noqa: E402
from src.worldgen.bake import bake_to_grid, nearest_cell_per_tile
from src.worldgen.config.presets import PRESETS
from src.worldgen.config.worldgen_config import WorldgenConfig
from src.worldgen.pipeline import WorldgenPipeline


def _run_seed(seed: int, size: int, config: WorldgenConfig) -> None:
    """Generate one world and print mesh/grid land fractions."""
    ctx = WorldgenPipeline(config).run(seed=seed, size=size)
    nearest = nearest_cell_per_tile(ctx.geometry, size=ctx.config.size)
    grid = bake_to_grid(ctx.fields, nearest)

    mesh_land_pct = 100.0 * float(ctx.fields.is_land.mean())
    grid_land_pct = 100.0 * float(grid.is_land.mean())
    elev_span = float(ctx.fields.elevation.max() - ctx.fields.elevation.min())
    print(
        f"  seed {seed:>6}: mesh_land={mesh_land_pct:5.1f}%  "
        f"grid_land={grid_land_pct:5.1f}%  elev_span={elev_span:.3f}"
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for seed scanning."""
    parser = argparse.ArgumentParser(
        description="Scan seeds and print land-fraction summaries."
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
    """Run the seed scan and print one summary line per seed."""
    args = parse_args()
    seeds: list[int] = args.seeds or [
        random.randint(0, 2**31 - 1) for _ in range(args.count)
    ]
    config = PRESETS[args.preset] if args.preset else WorldgenConfig()

    preset_label = args.preset or "default"
    print(f"Scanning {len(seeds)} seeds  size={args.size}  preset={preset_label}\n")

    for seed in seeds:
        _run_seed(seed, args.size, config)

    print("\nDone.")


if __name__ == "__main__":
    main()
