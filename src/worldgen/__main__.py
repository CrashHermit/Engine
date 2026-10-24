"""Command-line diagnostics for generated continuous worlds."""

import argparse
from dataclasses import replace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.render.layers import LAYERS
from src.worldgen.render.viewer import render_world


def main() -> None:
    config = WorldgenConfig()
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=config.seed)
    parser.add_argument("--frequency", type=int, default=config.subdivision_frequency)
    parser.add_argument("--field-frequency", type=int, default=80)
    parser.add_argument("--radius-m", type=float, default=config.planet.radius_m)
    parser.add_argument(
        "--rotation-axis",
        nargs=3,
        type=float,
        default=config.planet.rotation_axis,
        metavar=("X", "Y", "Z"),
        help="Planetary north axis; any nonzero Cartesian direction",
    )
    parser.add_argument(
        "--wind-speed-m-s",
        type=float,
        default=config.climate.circulation.base_speed_m_s,
        help="Reference prevailing wind speed, independent of plate motion",
    )
    parser.add_argument(
        "--equator-temperature-c",
        type=float,
        default=config.climate.temperature.equator_temperature_c,
        help="Latitude temperature baseline at the unit-sphere equator (Celsius)",
    )
    parser.add_argument(
        "--pole-temperature-c",
        type=float,
        default=config.climate.temperature.pole_temperature_c,
        help="Latitude temperature baseline at the unit-sphere poles (Celsius)",
    )
    parser.add_argument("--layer", choices=LAYERS, default="elevation")
    parser.add_argument("--terrain-relief", action="store_true")
    parser.add_argument("--vertical-exaggeration", type=float, default=1.0)
    parser.add_argument(
        "--water",
        "--sea-level",
        dest="sea_level",
        action="store_true",
        help="Show the sea-level water surface and enable terrain relief",
    )
    parser.add_argument("--elevation-min", type=float)
    parser.add_argument("--elevation-max", type=float)
    parser.add_argument(
        "--no-hex-edges", action="store_true", help="Start with cell outlines hidden"
    )
    parser.add_argument(
        "--hex-samples",
        action="store_true",
        help="Color elevation only at the configured hex centers",
    )
    parser.add_argument("--off-screen", action="store_true")
    parser.add_argument("--screenshot")
    parser.add_argument("--rotation-gif")
    parser.add_argument("--rotation-frames", type=int, default=120)
    parser.add_argument("--rotation-fps", type=float, default=24.0)
    parser.add_argument(
        "--plate-count", type=int, default=config.geology.plates.plate_count
    )
    parser.add_argument(
        "--continental-seeds", type=int, default=config.geology.crust.continental_seeds
    )
    parser.add_argument(
        "--oceanic-seeds", type=int, default=config.geology.crust.oceanic_seeds
    )
    parser.add_argument(
        "--plate-transition-half-width-percent",
        type=float,
        default=config.geology.plates.transition_half_width_percent,
        help="Plate overlap half-width as a percentage of radius in source space",
    )
    parser.add_argument(
        "--opening-smoothing-width",
        type=float,
        default=config.geology.boundary_motion.opening_smoothing_width,
        help="Positive convergence/divergence smoothing width in motion units",
    )
    parser.add_argument(
        "--crust-transition-half-width-percent",
        type=float,
        default=config.geology.crust.transition_half_width_percent,
    )
    parser.add_argument(
        "--collision-midpoint",
        type=float,
        default=config.geology.material_blend.midpoint,
    )
    parser.add_argument(
        "--collision-transition-width",
        type=float,
        default=config.geology.material_blend.transition_width,
    )
    parser.add_argument(
        "--subduction-trench-depth-multiplier",
        type=float,
        default=config.relief.tectonic.subduction_trench_depth_multiplier,
        help="Scale trench depth independently of subduction arcs and convergence",
    )
    parser.add_argument(
        "--tectonic-motion-response-scale",
        type=float,
        default=config.relief.tectonic.motion_response_scale,
        help="Motion scale for smooth relief saturation; larger values weaken response",
    )
    parser.add_argument(
        "--terrain-variation-percent",
        type=float,
        default=config.relief.variation.amplitude_percent,
    )
    volcanic_defaults = config.relief.volcanism
    parser.add_argument(
        "--volcanic-height-percent",
        type=float,
        default=volcanic_defaults.relief_height_percent,
        help="Maximum volcanic relief as a percentage of planet radius",
    )
    parser.add_argument(
        "--volcanic-candidate-count",
        type=int,
        default=volcanic_defaults.candidate_count,
        help="Number of world-space suitability candidates for volcanic placement",
    )
    parser.add_argument(
        "--hotspot-count",
        type=int,
        default=volcanic_defaults.hotspot_count,
        help="Number of intraplate volcanic rods",
    )
    parser.add_argument(
        "--tectonic-volcano-count",
        type=int,
        default=volcanic_defaults.tectonic_count,
        help="Number of tectonic volcanic rods",
    )
    parser.add_argument(
        "--hotspot-placement-bias",
        type=float,
        default=volcanic_defaults.hotspot_bias,
        help="Concentration of intraplate rods toward suitable candidates",
    )
    parser.add_argument(
        "--tectonic-placement-bias",
        type=float,
        default=volcanic_defaults.tectonic_bias,
        help="Concentration of tectonic rods toward suitable candidates",
    )
    parser.add_argument(
        "--coastal-shelf-influence-span",
        type=float,
        default=config.relief.coastal.shelf.influence_span,
        help="Shelf span in continental-influence units, not geographic distance",
    )
    parser.add_argument(
        "--ridge-detail-blend",
        type=float,
        default=config.relief.ridge_detail.blend,
        help="Collision crest blend: 0 boundary-centered, 1 distributed ridge detail",
    )
    parser.add_argument(
        "--plate-min-speed",
        type=float,
        default=config.geology.plates.motion.min_angular_speed,
    )
    parser.add_argument(
        "--plate-max-speed",
        type=float,
        default=config.geology.plates.motion.max_angular_speed,
    )
    args = parser.parse_args()

    config = replace(
        config,
        seed=args.seed,
        subdivision_frequency=args.frequency,
        planet=replace(
            config.planet,
            radius_m=args.radius_m,
            rotation_axis=tuple(args.rotation_axis),
        ),
        climate=replace(
            config.climate,
            circulation=replace(
                config.climate.circulation, base_speed_m_s=args.wind_speed_m_s
            ),
            temperature=replace(
                config.climate.temperature,
                equator_temperature_c=args.equator_temperature_c,
                pole_temperature_c=args.pole_temperature_c,
            ),
        ),
        geology=replace(
            config.geology,
            boundary_motion=replace(
                config.geology.boundary_motion,
                opening_smoothing_width=args.opening_smoothing_width,
            ),
            plates=replace(
                config.geology.plates,
                plate_count=args.plate_count,
                transition_half_width_percent=args.plate_transition_half_width_percent,
                motion=replace(
                    config.geology.plates.motion,
                    min_angular_speed=args.plate_min_speed,
                    max_angular_speed=args.plate_max_speed,
                ),
            ),
            crust=replace(
                config.geology.crust,
                continental_seeds=args.continental_seeds,
                oceanic_seeds=args.oceanic_seeds,
                transition_half_width_percent=args.crust_transition_half_width_percent,
            ),
            material_blend=replace(
                config.geology.material_blend,
                midpoint=args.collision_midpoint,
                transition_width=args.collision_transition_width,
            ),
        ),
        relief=replace(
            config.relief,
            tectonic=replace(
                config.relief.tectonic,
                subduction_trench_depth_multiplier=args.subduction_trench_depth_multiplier,
                motion_response_scale=args.tectonic_motion_response_scale,
            ),
            coastal=replace(
                config.relief.coastal,
                shelf=replace(
                    config.relief.coastal.shelf,
                    influence_span=args.coastal_shelf_influence_span,
                ),
            ),
            ridge_detail=replace(
                config.relief.ridge_detail, blend=args.ridge_detail_blend
            ),
            variation=replace(
                config.relief.variation,
                amplitude_percent=args.terrain_variation_percent,
            ),
            volcanism=replace(
                config.relief.volcanism,
                candidate_count=args.volcanic_candidate_count,
                hotspot_count=args.hotspot_count,
                tectonic_count=args.tectonic_volcano_count,
                hotspot_bias=args.hotspot_placement_bias,
                tectonic_bias=args.tectonic_placement_bias,
                relief_height_percent=args.volcanic_height_percent,
            ),
        ),
    )
    world = generate_world(config)
    print(f"seed: {args.seed}")
    print(f"frequency: {args.frequency}")
    print(f"planet radius (m): {config.planet.radius_m}")
    print(f"partition: continuous Voronoi")
    print(f"plate seeds: {config.geology.plates.plate_count}")
    print(
        f"crust seeds: {config.geology.crust.continental_seeds + config.geology.crust.oceanic_seeds}"
    )
    print(f"cells: {len(world.mesh.vertices)}")
    print(f"faces: {len(world.mesh.faces)}")

    elevation_range = None
    if args.elevation_min is not None or args.elevation_max is not None:
        vertices, _ = generate_icosphere(args.field_frequency)
        dense = world.field.sample_world(vertices)
        values = (
            np.concatenate(
                (
                    world.elevation.elevation,
                    world.elevation.coastal_elevation,
                    dense.elevation.elevation,
                    dense.elevation.coastal_elevation,
                )
            )
            * config.planet.radius_m
        )
        low = min(float(np.min(values, initial=0.0)), 0.0)
        high = max(float(np.max(values, initial=0.0)), 0.0)
        if low == high:
            low, high = -1e-12, 1e-12
        elevation_range = (
            low if args.elevation_min is None else args.elevation_min,
            high if args.elevation_max is None else args.elevation_max,
        )
    render_world(
        world,
        layer=args.layer,
        off_screen=args.off_screen,
        terrain_relief=args.terrain_relief,
        vertical_exaggeration=args.vertical_exaggeration,
        sea_level=args.sea_level,
        hex_edges=not args.no_hex_edges,
        continuous_field=not args.hex_samples,
        field_frequency=args.field_frequency,
        screenshot=args.screenshot,
        rotation_gif=args.rotation_gif,
        rotation_frames=args.rotation_frames,
        rotation_fps=args.rotation_fps,
        elevation_range=elevation_range,
        rebuild_config=config,
    )


if __name__ == "__main__":
    main()
