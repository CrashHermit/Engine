"""Compare a Cartesian regional source field with its scalar warp composition."""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.worldgen.elevation.profiles import (
    collision_profile,
    divergent_profile,
    shear_profile,
)
from src.worldgen.field.noise import NoiseConfig
from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.region_overlap import RegionOverlapField
from src.worldgen.field.regions import WarpedVoronoiField, build_warped_voronoi_field
from src.worldgen.field.warp import ShearWarpConfig
from src.worldgen.geology.config import PlateMotionConfig
from src.worldgen.geology.motion import generate_plate_motion
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.geometry.rotation import rotational_velocity

WORLD_SEEDS = (123, 2026, 31415)
CASE_IDS = ("source-field", "warped-scalar")
CASE_TITLES = {
    "source-field": "Source-space regional field",
    "warped-scalar": "Scalar field composed through warp",
}
NOISE_CONFIG = NoiseConfig(
    octaves=3, base_frequency=1.2, lacunarity=2.0, persistence=0.5
)
WARP_CONFIG = ShearWarpConfig(iterations=4, amplitude=0.24, lacunarity=1.7, gain=0.65)
SEED_COUNT = 32
TRANSITION_HALF_WIDTH = 0.12
PROFILE_WIDTH = 0.12
SAMPLE_BLOCK_SIZE = 1024


@dataclass(frozen=True, slots=True)
class ComparisonWorld:
    """A warped source partition and its source-space regional interactions."""

    regions: WarpedVoronoiField
    influence: RegionInfluenceField
    overlap: RegionOverlapField
    angular_velocity: np.ndarray


@dataclass(frozen=True, slots=True)
class FieldSample:
    """Categorical ownership and dense source-field diagnostics."""

    ownership: np.ndarray
    opening: np.ndarray
    sliding: np.ndarray
    convergence: np.ndarray
    divergence: np.ndarray
    shear: np.ndarray
    elevation: np.ndarray
    region_overlap: np.ndarray


def build_world(seed: int) -> ComparisonWorld:
    streams = np.random.SeedSequence(seed).spawn(3)
    regions = build_warped_voronoi_field(
        SEED_COUNT,
        rng=np.random.default_rng(streams[0]),
        noise_seed=seed + 3000,
        noise_config=NOISE_CONFIG,
        warp_config=WARP_CONFIG,
    )
    angular_velocity = generate_plate_motion(
        regions.voronoi.seeds,
        PlateMotionConfig(),
        rng=np.random.default_rng(streams[2]),
    )
    influence = RegionInfluenceField(
        regions.voronoi,
        RegionInfluenceConfig(transition_half_width=TRANSITION_HALF_WIDTH),
    )
    return ComparisonWorld(
        regions, influence, RegionOverlapField(influence), angular_velocity
    )


def evaluate_relief(
    plane_distance: np.ndarray,
    opening: np.ndarray,
    sliding: np.ndarray,
    *,
    width: float = PROFILE_WIDTH,
) -> np.ndarray:
    """Evaluate symmetric source-space diagnostic profiles for sparse pairs."""
    distance = np.abs(plane_distance)
    if len(distance) == 0:
        return np.empty(0, dtype=np.float64)
    broad = np.empty(len(distance), dtype=np.float64)
    crest = np.empty(len(distance), dtype=np.float64)
    for index, value in enumerate(distance):
        broad[index], crest[index] = collision_profile(float(value), width, 0.2)
    divergent = np.fromiter(
        (
            divergent_profile(float(value), width, continental=True)
            for value in distance
        ),
        dtype=np.float64,
        count=len(distance),
    )
    shear_profile_values = np.fromiter(
        (shear_profile(float(value), width) for value in distance),
        dtype=np.float64,
        count=len(distance),
    )
    collision = np.maximum(-opening, 0.0) * (0.65 * broad + 0.35 * crest)
    rift = np.maximum(opening, 0.0) * divergent
    return collision + rift + 0.15 * sliding * shear_profile_values


def _sample_source(world: ComparisonWorld, positions: np.ndarray) -> FieldSample:
    points = np.asarray(positions, dtype=np.float64)
    count = len(points)
    owner = np.empty(count, dtype=np.int64)
    dense = {
        name: np.zeros(count, dtype=np.float64)
        for name in (
            "opening",
            "sliding",
            "convergence",
            "divergence",
            "shear",
            "elevation",
            "region_overlap",
        )
    }
    for start in range(0, count, SAMPLE_BLOCK_SIZE):
        stop = min(start + SAMPLE_BLOCK_SIZE, count)
        block = points[start:stop]
        region_sample = world.influence.sample(block)
        owner[start:stop] = region_sample.voronoi.owner_seed_id
        overlap = world.overlap.sample_from_regions(region_sample)
        if not len(overlap.query_indices):
            continue
        q = overlap.query_indices
        pairs = overlap.region_pairs
        source_positions = block[q]
        va = rotational_velocity(source_positions, world.angular_velocity[pairs[:, 0]])
        vb = rotational_velocity(source_positions, world.angular_velocity[pairs[:, 1]])
        relative = vb - va
        opening = np.einsum("ij,ij->i", relative, overlap.normals)
        tangent = relative - opening[:, None] * overlap.normals
        sliding = np.linalg.norm(tangent, axis=1)
        convergence = np.maximum(-opening, 0.0)
        divergence = np.maximum(opening, 0.0)
        relief = evaluate_relief(overlap.plane_distance, opening, sliding)
        weights = overlap.influence
        block_count = stop - start
        for name, values in (
            ("opening", opening),
            ("sliding", sliding),
            ("convergence", convergence),
            ("divergence", divergence),
            ("shear", sliding),
            ("elevation", relief),
            ("region_overlap", np.ones_like(weights)),
        ):
            dense[name][start:stop] = np.bincount(
                q, weights=weights * values, minlength=block_count
            )
    for values in (owner, *dense.values()):
        values.setflags(write=False)
    return FieldSample(owner, **dense)


def sample_comparison(
    world: ComparisonWorld, positions: np.ndarray
) -> dict[str, FieldSample]:
    """Compare source values at p with the same scalar source field at W(p)."""
    points = np.asarray(positions, dtype=np.float64)
    source = _sample_source(world, points)
    warped_points = world.regions.warp.sample(points)
    warped = _sample_source(world, warped_points)
    return {"source-field": source, "warped-scalar": warped}


def check_comparison() -> None:
    points = np.random.default_rng(812).uniform(-1.0, 1.0, (1307, 3))
    world = build_world(2026)
    full = sample_comparison(world, points)
    chunked = [
        sample_comparison(world, points[:500]),
        sample_comparison(world, points[500:]),
    ]
    permutation = np.random.default_rng(71).permutation(len(points))
    reordered = sample_comparison(world, points[permutation])
    for case in CASE_IDS:
        for field in FieldSample.__dataclass_fields__:
            values = getattr(full[case], field)
            np.testing.assert_allclose(
                np.concatenate([getattr(item[case], field) for item in chunked]), values
            )
            np.testing.assert_allclose(
                getattr(reordered[case], field), values[permutation]
            )
    empty = sample_comparison(world, np.empty((0, 3)))
    assert all(len(getattr(empty[case], "elevation")) == 0 for case in CASE_IDS)
    assert np.isfinite(full["warped-scalar"].elevation).all()

    signed_limits = _shared_field_limits([np.array([-0.1431, 0.3801])], signed=True)
    assert signed_limits[0] <= -0.1431 and signed_limits[1] >= 0.3801


def _regular_xy_points(
    resolution: int, lower: float = -1.0, upper: float = 1.0
) -> np.ndarray:
    axis = np.linspace(lower, upper, resolution)
    x, y = np.meshgrid(axis, axis)
    return np.column_stack((x.ravel(), y.ravel(), np.zeros(x.size)))


def _palette() -> np.ndarray:
    return np.rint(
        plt.get_cmap("gist_ncar")(np.linspace(0.05, 0.95, SEED_COUNT))[:, :3] * 255
    ).astype(np.uint8)


def _draw_owner_outlines(axis, ownership: np.ndarray, resolution: int) -> None:
    from matplotlib.collections import LineCollection

    coordinates = np.linspace(-1.0, 1.0, resolution)
    owners = ownership.reshape((resolution, resolution))
    step = coordinates[1] - coordinates[0]
    row, column = np.nonzero(owners[:, :-1] != owners[:, 1:])
    x = 0.5 * (coordinates[column] + coordinates[column + 1])
    y = coordinates[row]
    vertical = np.stack(
        (np.column_stack((x, y - 0.5 * step)), np.column_stack((x, y + 0.5 * step))),
        axis=1,
    )
    row, column = np.nonzero(owners[:-1, :] != owners[1:, :])
    y = 0.5 * (coordinates[row] + coordinates[row + 1])
    x = coordinates[column]
    horizontal = np.stack(
        (np.column_stack((x - 0.5 * step, y)), np.column_stack((x + 0.5 * step, y))),
        axis=1,
    )
    axis.add_collection(
        LineCollection(
            np.concatenate((vertical, horizontal)),
            colors="black",
            linewidths=0.45,
            alpha=0.85,
        )
    )


def _render_ownership(
    ownership: np.ndarray,
    resolution: int,
    output: Path,
    palette: np.ndarray,
    *,
    title: str,
) -> None:
    fig, axis = plt.subplots(figsize=(10, 9), layout="constrained")
    axis.imshow(
        palette[ownership].reshape((resolution, resolution, 3)),
        origin="lower",
        extent=(-1, 1, -1, 1),
        interpolation="nearest",
    )
    _draw_owner_outlines(axis, ownership, resolution)
    axis.set(title=title, xlabel="x", ylabel="y", aspect="equal")
    fig.savefig(output, dpi=100)
    plt.close(fig)


def _render_globe(
    points: np.ndarray,
    faces: np.ndarray,
    elevation: np.ndarray,
    output: Path,
    *,
    limits: tuple[float, float],
    radial_factor: float,
) -> None:
    import pyvista as pv

    displaced = points * (1.0 + radial_factor * elevation[:, None])
    cells = np.column_stack((np.full(len(faces), 3, dtype=np.int64), faces)).ravel()
    surface = pv.PolyData(displaced, cells)
    surface.point_data["elevation"] = elevation
    plotter = pv.Plotter(off_screen=True, shape=(1, 2), window_size=(1400, 700))
    try:
        for column, direction in enumerate(((1.6, -2.4, 1.2), (-1.8, 1.6, -0.6))):
            plotter.subplot(0, column)
            plotter.set_background("#f4f6f8")
            plotter.add_mesh(
                surface,
                scalars="elevation",
                cmap="BrBG_r",
                clim=limits,
                show_scalar_bar=column == 1,
                smooth_shading=True,
            )
            plotter.camera_position = (direction, (0, 0, 0), (0, 0, 1))
            plotter.enable_parallel_projection()
            plotter.camera.parallel_scale = 1.1
        plotter.screenshot(str(output))
    finally:
        plotter.close()


def _field_metrics(values: np.ndarray) -> dict[str, float]:
    return {
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "rms": float(np.sqrt(np.mean(values**2))),
    }


def _shared_field_limits(
    arrays: list[np.ndarray], *, signed: bool
) -> tuple[float, float]:
    """Return shared zero-centered limits for signed diagnostics."""
    extent = max(float(np.max(np.abs(values), initial=0.0)) for values in arrays)
    return (-extent if signed else 0.0, extent)


def _run_experiment(output: Path, frequency: int, slice_resolution: int) -> None:
    output.mkdir(parents=True, exist_ok=True)
    sphere, faces = generate_icosphere(frequency)
    slice_points = _regular_xy_points(slice_resolution)
    worlds = []
    for seed in WORLD_SEEDS:
        started = perf_counter()
        world = build_world(seed)
        slice_samples = sample_comparison(world, slice_points)
        sphere_samples = sample_comparison(world, sphere)
        probe_points = np.random.default_rng(812).uniform(-1.0, 1.0, (1307, 3))
        probe_samples = sample_comparison(world, probe_points)
        filename = f"motion-{seed}-fields.npz"
        arrays = {
            "seeds": world.regions.voronoi.seeds,
            "angular_velocity": world.angular_velocity,
            "slice_points": slice_points,
            "sphere_points": sphere,
            "slice_ownership": slice_samples[CASE_IDS[0]].ownership,
            "sphere_ownership": sphere_samples[CASE_IDS[0]].ownership,
        }
        for case in CASE_IDS:
            for surface, samples in (
                ("slice", slice_samples),
                ("sphere", sphere_samples),
            ):
                for field in FieldSample.__dataclass_fields__:
                    arrays[f"{case}_{surface}_{field}"] = getattr(samples[case], field)
        np.savez(output / filename, **arrays)
        worlds.append(
            {
                "seed": seed,
                "world": world,
                "slice": slice_samples,
                "sphere": sphere_samples,
                "probe": probe_samples,
                "fields_file": filename,
            }
        )
        print(
            f"[{seed}] Sampled regional source and scalar-warp fields in {perf_counter() - started:.2f}s.",
            flush=True,
        )
    display_fields = (
        "opening",
        "sliding",
        "convergence",
        "divergence",
        "shear",
        "elevation",
        "region_overlap",
    )
    common = {
        name: _shared_field_limits(
            [
                getattr(samples[case], name)
                for entry in worlds
                for samples in (entry["slice"], entry["sphere"])
                for case in CASE_IDS
            ],
            signed=name in ("opening", "elevation"),
        )
        for name in display_fields
    }
    elevation_limits = common["elevation"]
    radial = 0.06 / max(abs(elevation_limits[0]), elevation_limits[1], 1e-12)
    palette = _palette()
    manifest_worlds = []
    for entry in worlds:
        seed = entry["seed"]
        slice_samples = entry["slice"]
        sphere_samples = entry["sphere"]
        ownership_file = f"motion-{seed}-ownership.png"
        _render_ownership(
            slice_samples[CASE_IDS[0]].ownership,
            slice_resolution,
            output / ownership_file,
            palette,
            title=f"Source-field ownership · seed {seed}",
        )
        records = []
        for case in CASE_IDS:
            samples = slice_samples[case]
            sphere_elevation = sphere_samples[case].elevation
            images = {}
            for field in display_fields:
                name = f"motion-{seed}-{case}-{field}.png"
                images[field] = name
                vals = getattr(samples, field)
                fig, ax = plt.subplots(figsize=(9, 8), layout="constrained")
                cmap = (
                    "RdBu_r"
                    if field == "opening"
                    else ("magma" if field != "elevation" else "BrBG_r")
                )
                image = ax.imshow(
                    vals.reshape((slice_resolution, slice_resolution)),
                    origin="lower",
                    extent=(-1, 1, -1, 1),
                    cmap=cmap,
                    vmin=common[field][0],
                    vmax=common[field][1],
                )
                _draw_owner_outlines(ax, samples.ownership, slice_resolution)
                ax.set(title=f"{CASE_TITLES[case]} · {field}", aspect="equal")
                fig.colorbar(image, ax=ax, orientation="horizontal", pad=0.08)
                fig.savefig(output / name, dpi=100)
                plt.close(fig)
            images["globe"] = f"motion-{seed}-{case}-globe.png"
            _render_globe(
                sphere,
                faces,
                sphere_elevation,
                output / images["globe"],
                limits=common["elevation"],
                radial_factor=radial,
            )
            records.append(
                {
                    "id": case,
                    "title": CASE_TITLES[case],
                    "description": "All regional interactions are evaluated in Cartesian source coordinates; only the scalar result is composed through W.",
                    "images": images,
                    "metrics": {
                        field: _field_metrics(getattr(samples, field))
                        for field in (
                            "opening",
                            "sliding",
                            "convergence",
                            "divergence",
                            "shear",
                            "elevation",
                            "region_overlap",
                        )
                    },
                }
            )
        manifest_worlds.append(
            {
                "seed": seed,
                "ownership_image": ownership_file,
                "fields_file": entry["fields_file"],
                "cases": records,
                "probe_metrics": {
                    case: {
                        field: _field_metrics(getattr(entry["probe"][case], field))
                        for field in ("opening", "sliding", "elevation")
                    }
                    for case in CASE_IDS
                },
            }
        )
    manifest = {
        "title": "Regional source field and scalar warp composition",
        "cases": list(CASE_IDS),
        "worlds": manifest_worlds,
        "settings": {
            "seeds": list(WORLD_SEEDS),
            "seed_count": SEED_COUNT,
            "transition_half_width_source": TRANSITION_HALF_WIDTH,
            "profile_width_source": PROFILE_WIDTH,
            "noise": {
                "octaves": NOISE_CONFIG.octaves,
                "base_frequency": NOISE_CONFIG.base_frequency,
            },
            "warp": {
                "iterations": WARP_CONFIG.iterations,
                "amplitude": WARP_CONFIG.amplitude,
                "lacunarity": WARP_CONFIG.lacunarity,
                "gain": WARP_CONFIG.gain,
            },
            "field_limits": {key: list(value) for key, value in common.items()},
            "scalar_composition": "G_source(W(p))",
        },
        "profile_recipe": {
            "crust_assumption": "uniform continental",
            "collision_crest_width_fraction": 0.2,
            "collision_broad_crest_mix": [0.65, 0.35],
            "shear_relief_fraction": 0.15,
        },
    }
    (output / "motion-space-results.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    _publish_gallery(output)


def _publish_gallery(output: Path) -> None:
    template = Path(__file__).with_name("motion_space_compare.html")
    (output / "motion-space.html").write_text(
        template.read_text(encoding="utf-8"), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("/tmp/domain-warp-voronoi-site")
    )
    parser.add_argument("--frequency", type=int, default=40)
    parser.add_argument("--slice-resolution", type=int, default=128)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_comparison()
        print("Regional source/scalar warp comparison checks passed.")
    else:
        _run_experiment(args.output, args.frequency, args.slice_resolution)


if __name__ == "__main__":
    main()
