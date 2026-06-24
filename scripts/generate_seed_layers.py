#!/usr/bin/env python3
"""
Generate images of different seeds with all their layers for visualization.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

OUTPUT_DIR = Path("output/seed_layers")
SEEDS = [42, 123, 456, 789, 999]
SIZE = 100
RESOLUTION = 512  # High-quality render
SCALE = 2  # Pixels per node

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for seed in SEEDS:
        seed_dir = OUTPUT_DIR / f"seed_{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"Generating all layers for seed {seed}...")
        print(f"{'='*60}")

        cmd = [
            "uv", "run", "python", "scripts/export_worldgen.py",
            "--seed", str(seed),
            "--size", str(SIZE),
            "--resolution", str(RESOLUTION),
            "--scale", str(SCALE),
            "--all-layers",
            "-o", str(seed_dir)
        ]

        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        if result.returncode != 0:
            print(f"ERROR: Failed to generate layers for seed {seed}")
            return

    print(f"\n{'='*60}")
    print(f"✓ Generated all seed layer images in {OUTPUT_DIR}")
    print(f"{'='*60}")
    print(f"\nSeeds generated: {', '.join(str(s) for s in SEEDS)}")
    print(f"Each seed has all visualization layers exported to separate PNG files.")

if __name__ == "__main__":
    main()
