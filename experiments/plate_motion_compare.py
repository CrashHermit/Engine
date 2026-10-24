"""Compare seed-axis rotations, random Euler poles, and constant regional motion."""

import argparse
import json
from dataclasses import replace
from pathlib import Path
from functools import partial

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.relief.generate import generate_source_relief_field
from src.worldgen.field.boundary_motion import BoundaryMotionField
from src.worldgen.field.boundary_transport import TransportedBoundaryVectorField
from src.worldgen.field.boundary_vector import BoundaryVectorField
from src.worldgen.field.interaction import BoundaryInteractionField
from src.worldgen.field.differential import VectorSample
from src.worldgen.field.motion import RegionRotationField
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.geometry.rotation import rotational_velocity
from src.worldgen.generate import generate_world_field
from src.worldgen.generate import generate_world
from src.worldgen.surface.field import SurfaceField
from src.worldgen.world import WorldField

CASES = (
    ("seed-axis", "Seed-axis Euler rotation"),
    ("random-pole", "Independent random Euler poles"),
    ("translation", "Constant regional translation"),
)
EXAGGERATION = 25.0


def _unit_directions(count: int, seed: int) -> np.ndarray:
    directions = np.random.default_rng(seed).normal(size=(count, 3))
    return directions / np.linalg.norm(directions, axis=1, keepdims=True)


def _comparison_world(
    baseline: WorldField, config: WorldgenConfig, mode: str, seed: int
) -> WorldField:
    geology = baseline.geology
    angular = geology.rotations.angular_velocity
    speeds = np.linalg.norm(angular, axis=1)

    if mode == "seed-axis":
        vectors = geology.regions.voronoi.seeds.copy()
        vectors *= (speeds / np.linalg.norm(vectors, axis=1))[:, None]
        rotational = True
    elif mode == "random-pole":
        vectors = _unit_directions(len(speeds), seed + 10_001) * speeds[:, None]
        rotational = True
    else:
        vectors = _unit_directions(len(speeds), seed + 20_003) * speeds[:, None]
        rotational = False

    def sample_region_vectors(
        positions: np.ndarray, region_ids: np.ndarray
    ) -> np.ndarray:
        if rotational:
            return rotational_velocity(positions, vectors[region_ids])
        return vectors[region_ids]

    if rotational:
        sample_region_jacobians = RegionRotationField(
            geology.regions.voronoi, vectors
        ).sample_regions_with_jacobian
    else:

        def sample_region_jacobians(
            positions: np.ndarray, region_ids: np.ndarray
        ) -> VectorSample:
            return VectorSample(
                sample_region_vectors(positions, region_ids),
                np.zeros((len(positions), 3, 3), dtype=np.float64),
            )

    motion = BoundaryMotionField(
        TransportedBoundaryVectorField(
            BoundaryVectorField(
                geology.overlap, sample_region_vectors, sample_region_jacobians
            ),
            source_to_world_with_jacobian=baseline.warp.inverse_with_jacobian,
            source_to_world_with_hessian=baseline.warp.inverse_with_hessian,
        )
    )
    comparison_geology = replace(
        geology,
        motion=motion,
        interaction=BoundaryInteractionField(motion),
    )
    source_relief = generate_source_relief_field(
        config.relief,
        geology=comparison_geology,
        noise_seeds=baseline.source_relief.coastal.influence_span_noise_seeds,
    )
    return WorldField(
        geology=comparison_geology,
        source_relief=source_relief,
        warp=baseline.warp,
        impact_relief=baseline.impact_relief,
        volcanism=baseline.volcanism,
        climate=baseline.climate,
    )


def _mesh(points: np.ndarray, faces: np.ndarray, values: np.ndarray, name: str):
    import pyvista as pv

    cells = np.column_stack((np.full(len(faces), 3, dtype=np.int64), faces)).ravel()
    surface = pv.PolyData(points, cells)
    surface.point_data[name] = values
    return surface


def _render(
    samples: list[dict[str, object]],
    points: np.ndarray,
    faces: np.ndarray,
    radius_m: float,
    output: Path,
    *,
    convergence: bool,
) -> None:
    import pyvista as pv

    field_name = "convergence" if convergence else "elevation_m"
    arrays = [
        (
            entry[case]["sample"].geology.convergence
            if convergence
            else entry[case]["sample"].elevation.elevation * radius_m
        )
        for entry in samples
        for case, _ in CASES
    ]
    if convergence:
        limits = (0.0, float(np.percentile(np.concatenate(arrays), 99.5)))
        limits = (limits[0], max(limits[1], 1e-12))
    else:
        limits = (
            min(float(np.min(values)) for values in arrays),
            max(float(np.max(values)) for values in arrays),
        )

    plotter = pv.Plotter(
        off_screen=True,
        shape=(len(samples), len(CASES)),
        window_size=(1650, 550 * len(samples)),
    )
    try:
        for row, entry in enumerate(samples):
            for column, (case, title) in enumerate(CASES):
                sample = entry[case]["sample"]
                if convergence:
                    values = sample.geology.convergence
                    mesh_points = points
                    cmap = "inferno"
                else:
                    values = sample.elevation.elevation * radius_m
                    mesh_points = points * (
                        1.0 + EXAGGERATION * values[:, None] / radius_m
                    )
                    cmap = "BrBG_r"
                surface = _mesh(mesh_points, faces, values, field_name)
                plotter.subplot(row, column)
                plotter.set_background("#f4f6f8")
                plotter.add_mesh(
                    surface,
                    scalars=field_name,
                    cmap=cmap,
                    clim=limits,
                    smooth_shading=True,
                    show_scalar_bar=(row == 0 and column == len(CASES) - 1),
                    scalar_bar_args={
                        "title": "Convergence" if convergence else "Elevation (m)",
                        "vertical": True,
                        "position_x": 0.84,
                        "position_y": 0.22,
                        "height": 0.56,
                        "width": 0.08,
                        "label_font_size": 8,
                        "title_font_size": 9,
                        "n_labels": 4,
                    },
                )
                plotter.add_text(
                    f"{title} · seed {entry['seed']}", font_size=11, color="black"
                )
                plotter.camera_position = ((2.7, -2.4, 1.7), (0.0, 0.0, 0.0), (0, 0, 1))
                plotter.enable_parallel_projection()
                plotter.camera.parallel_scale = 1.25
        plotter.screenshot(str(output))
    finally:
        plotter.close()


def run(output: Path, seeds: list[int], frequency: int) -> None:
    output.mkdir(parents=True, exist_ok=True)
    points, faces = generate_icosphere(frequency)
    reports: list[dict[str, object]] = []

    for seed in seeds:
        config = WorldgenConfig(seed=seed)
        baseline = generate_world_field(config)
        entry: dict[str, object] = {"seed": seed}
        report: dict[str, object] = {"seed": seed}
        for mode, _ in CASES:
            world = _comparison_world(baseline, config, mode, seed)
            sample = world.sample_world(points)
            elevation_m = sample.elevation.elevation * config.planet.radius_m
            convergence_m = sample.elevation.convergent_relief * config.planet.radius_m
            land = elevation_m > 0.0
            report[mode] = {
                "land_percent": float(100.0 * np.mean(land)),
                "land_with_over_100m_convergent_relief_percent": float(
                    100.0 * np.mean(convergence_m[land] > 100.0)
                ),
                "land_convergent_relief_p95_m": float(
                    np.percentile(convergence_m[land], 95.0)
                ),
                "land_convergent_relief_max_m": float(np.max(convergence_m[land])),
                "elevation_max_m": float(np.max(elevation_m)),
                "convergence_p95": float(
                    np.percentile(sample.geology.convergence, 95.0)
                ),
                "divergence_p95": float(np.percentile(sample.geology.divergence, 95.0)),
                "shear_p95": float(np.percentile(sample.geology.shear, 95.0)),
            }
            entry[mode] = {"sample": sample}
            print(f"sampled seed={seed} motion={mode}", flush=True)
        reports.append(report)
        reports[-1]["_entry"] = entry

    render_entries = [report.pop("_entry") for report in reports]
    _render(
        render_entries,
        points,
        faces,
        WorldgenConfig().planet.radius_m,
        output / "motion-model-elevation.png",
        convergence=False,
    )
    _render(
        render_entries,
        points,
        faces,
        WorldgenConfig().planet.radius_m,
        output / "motion-model-convergence.png",
        convergence=True,
    )
    (output / "motion-model-metrics.json").write_text(
        json.dumps(reports, indent=2), encoding="utf-8"
    )
    print(json.dumps(reports, indent=2))
    print(f"images and metrics: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("/tmp/plate-motion-comparison")
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=[123, 2026, 31415])
    parser.add_argument(
        "--viewer",
        choices=[case[0] for case in CASES],
        help="Open one comparison model in the existing interactive viewer",
    )
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--field-frequency", type=int, default=80)
    parser.add_argument(
        "--flank-width",
        type=float,
        choices=(1.0, 1.25, 1.5),
        default=1.0,
        help="Compare broader collision/ridge flanks while preserving axial widths",
    )
    parser.add_argument(
        "--collision-width-percent",
        type=float,
        help="Collision flank width; preserves the existing crest width",
    )
    parser.add_argument("--collision-height-percent", type=float)
    parser.add_argument(
        "--ridge-width-percent",
        type=float,
        help="Oceanic ridge width; preserves the existing axial width",
    )
    parser.add_argument("--ridge-height-percent", type=float)
    parser.add_argument("--off-screen", action="store_true")
    parser.add_argument("--screenshot")
    parser.add_argument("--frequency", type=int, default=20)
    args = parser.parse_args()
    if args.viewer is None:
        run(args.output, args.seeds, args.frequency)
        return

    from src.worldgen.render.viewer import render_world

    config = WorldgenConfig(seed=args.seed, subdivision_frequency=args.frequency)
    tectonic = config.relief.tectonic
    collision_width = (
        tectonic.collision.width_percent * args.flank_width
        if args.collision_width_percent is None
        else args.collision_width_percent
    )
    ridge_width = (
        tectonic.ridge.width_percent * args.flank_width
        if args.ridge_width_percent is None
        else args.ridge_width_percent
    )
    config = replace(
        config,
        relief=replace(
            config.relief,
            tectonic=replace(
                config.relief.tectonic,
                collision=replace(
                    config.relief.tectonic.collision,
                    width_percent=collision_width,
                    height_percent=(
                        tectonic.collision.height_percent
                        if args.collision_height_percent is None
                        else args.collision_height_percent
                    ),
                ),
                ridge=replace(
                    config.relief.tectonic.ridge,
                    width_percent=ridge_width,
                    height_percent=(
                        tectonic.ridge.height_percent
                        if args.ridge_height_percent is None
                        else args.ridge_height_percent
                    ),
                ),
                collision_crest_width_fraction=(
                    config.relief.tectonic.collision_crest_width_fraction
                    * tectonic.collision.width_percent
                    / collision_width
                ),
                ridge_axial_width_fraction=(
                    config.relief.tectonic.ridge_axial_width_fraction
                    * tectonic.ridge.width_percent
                    / ridge_width
                ),
            ),
        ),
    )
    baseline = generate_world(config)
    field = _comparison_world(baseline.field, config, args.viewer, args.seed)
    sample = field.sample_world(baseline.mesh.vertices)
    surface_field = SurfaceField(
        config.surface,
        partial(field.sample_elevation_meters, radius_m=baseline.radius_m),
        baseline.radius_m,
        partial(
            field.sample_elevation_meters_with_gradient, radius_m=baseline.radius_m
        ),
    )
    world = replace(
        baseline,
        field=field,
        geology=sample.geology,
        elevation=sample.elevation,
        surface_field=surface_field,
        surface=surface_field.sample(
            baseline.mesh.vertices,
            center_elevation=sample.elevation.elevation * baseline.radius_m,
        ),
    )
    render_world(
        world,
        field_frequency=args.field_frequency,
        terrain_relief=True,
        vertical_exaggeration=EXAGGERATION,
        hex_edges=False,
        off_screen=args.off_screen,
        screenshot=args.screenshot,
    )


if __name__ == "__main__":
    main()
