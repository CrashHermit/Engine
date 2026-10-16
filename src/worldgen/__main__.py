"""Command-line diagnostics for the current worldgen pipeline."""

import argparse
from dataclasses import replace

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.render.viewer import LAYERS, render_geology


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--frequency", type=int, default=20)
    parser.add_argument("--radius-m", type=float, default=6_371_000.0)
    parser.add_argument("--plate-irregularity", type=float, default=1.0)
    parser.add_argument("--plate-motion-scale", type=float, default=1.0)
    parser.add_argument("--plate-min-speed", type=float, default=0.05)
    parser.add_argument("--plate-max-speed", type=float, default=0.20)
    parser.add_argument("--crust-irregularity", type=float, default=1.0)
    parser.add_argument(
        "--plate-growth",
        choices=("priority-flood", "dijkstra"),
        default="priority-flood",
    )
    parser.add_argument(
        "--crust-growth",
        choices=("priority-flood", "dijkstra"),
        default="priority-flood",
    )
    parser.add_argument("--plate-flood-influence", type=float, default=1.1)
    parser.add_argument("--crust-flood-influence", type=float, default=1.1)
    parser.add_argument(
        "--layer",
        choices=LAYERS,
        default="plates",
    )
    parser.add_argument("--arrow-scale", type=float, default=0.08)
    parser.add_argument("--terrain-relief", action="store_true")
    parser.add_argument("--vertical-exaggeration", type=float, default=1.0)
    parser.add_argument("--sea-level", action="store_true")
    parser.add_argument("--elevation-min", type=float)
    parser.add_argument("--elevation-max", type=float)
    parser.add_argument(
        "--no-hex-edges", action="store_true", help="Start with cell outlines hidden"
    )
    parser.add_argument("--off-screen", action="store_true")
    parser.add_argument("--screenshot")
    args = parser.parse_args()
    config = WorldgenConfig(seed=args.seed, subdivision_frequency=args.frequency)
    config = replace(
        config,
        planet=replace(config.planet, radius_m=args.radius_m),
        geology=replace(
            config.geology,
            plates=replace(
                config.geology.plates,
                irregularity_strength=args.plate_irregularity,
                motion_scale=args.plate_motion_scale,
                min_angular_speed=args.plate_min_speed,
                max_angular_speed=args.plate_max_speed,
                growth_method=args.plate_growth,
                flood=replace(
                    config.geology.plates.flood, influence=args.plate_flood_influence
                ),
            ),
            crust=replace(
                config.geology.crust,
                irregularity_strength=args.crust_irregularity,
                growth_method=args.crust_growth,
                flood=replace(
                    config.geology.crust.flood, influence=args.crust_flood_influence
                ),
            ),
        ),
    )
    world = generate_world(config)
    print(f"seed: {args.seed}")
    print(f"frequency: {args.frequency}")
    print(f"planet radius (m): {config.planet.radius_m}")
    for name, growth in (
        ("plate", config.geology.plates),
        ("crust", config.geology.crust),
    ):
        print(f"{name} growth: {growth.growth_method}")
        if growth.growth_method == "priority-flood":
            print(f"{name} flood influence: {growth.flood.influence}")
        else:
            print(f"{name} irregularity: {growth.irregularity_strength}")
    print(f"cells: {len(world.mesh.vertices)}")
    print(f"faces: {len(world.mesh.faces)}")
    print(f"plates: {len(world.geology.plate_rotation)}")
    print(f"crust regions: {len(world.geology.crust.seed_indices)}")
    print(f"boundaries: {len(world.geology.boundary_edge_indices)}")
    render_geology(
        world,
        layer=args.layer,
        arrow_scale=args.arrow_scale,
        off_screen=args.off_screen,
        screenshot=args.screenshot,
        terrain_relief=args.terrain_relief,
        vertical_exaggeration=args.vertical_exaggeration,
        sea_level=args.sea_level,
        hex_edges=not args.no_hex_edges,
        elevation_range=(args.elevation_min, args.elevation_max)
        if args.elevation_min is not None
        else None,
    )


if __name__ == "__main__":
    main()
