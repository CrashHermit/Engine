"""Command-line diagnostics for the current worldgen pipeline."""

import argparse

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.render.geology import render_geology


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--frequency", type=int, default=20)
    parser.add_argument(
        "--layer",
        choices=(
            "plates",
            "intensity",
            "magma",
            "velocity",
            "convergence",
            "divergence",
            "shear",
        ),
        default="plates",
    )
    parser.add_argument("--arrow-scale", type=float, default=0.08)
    parser.add_argument("--off-screen", action="store_true")
    parser.add_argument("--screenshot")
    args = parser.parse_args()

    world = generate_world(
        WorldgenConfig(seed=args.seed, subdivision_frequency=args.frequency)
    )
    print(f"seed: {args.seed}")
    print(f"cells: {len(world.mesh.vertices)}")
    print(f"faces: {len(world.mesh.faces)}")
    print(f"plates: {len(world.geology.plate_rotation)}")
    print(f"boundaries: {len(world.geology.boundary_edge_indices)}")
    render_geology(
        world,
        layer=args.layer,
        arrow_scale=args.arrow_scale,
        off_screen=args.off_screen,
        screenshot=args.screenshot,
    )


if __name__ == "__main__":
    main()
