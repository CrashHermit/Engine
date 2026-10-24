"""Temporary source-space scalar-deformation diagnostic gallery generator."""

import argparse
import json
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from experiments.motion_space_compare import (
    _draw_owner_outlines,
    _palette,
    _render_globe,
    _render_ownership,
    _regular_xy_points,
)
from src.worldgen.relief.collision import collision_profile
from src.worldgen.relief.divergence import divergent_profile
from src.worldgen.relief.fault import fault_profile
from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.region_overlap import RegionOverlapField
from src.worldgen.field.boundary_vector import BoundaryVectorField
from src.worldgen.field.boundary_motion import BoundaryMotionField
from src.worldgen.field.boundary_response import BoundaryResponseField
from src.worldgen.field.compose import WarpedScalarField
from src.worldgen.field.interaction import BoundaryInteractionField
from src.worldgen.field.motion import RegionRotationField
from src.worldgen.field.noise import NoiseConfig
from src.worldgen.field.regions import build_warped_voronoi_field
from src.worldgen.field.warp import ShearWarpConfig
from src.worldgen.geology.motion import PlateMotionConfig, generate_plate_motion
from src.worldgen.geometry.icosphere import generate_icosphere

SEEDS = (123, 2026, 31415)
CASES = (("source", "Source-space response"), ("warped", "Warped scalar response"))
LAYERS = (
    "ownership",
    "influence",
    "convergence",
    "divergence",
    "shear",
    "elevation",
    "globe",
)
CHANNELS = ("convergence", "divergence", "shear")
TRANSITION_HALF_WIDTH = 0.12
PROFILE_WIDTH = 0.12
NOISE = NoiseConfig(octaves=3, base_frequency=1.2, lacunarity=2.0, persistence=0.5)
WARP = ShearWarpConfig(iterations=4, amplitude=0.24, lacunarity=1.7, gain=0.65)
BLOCK = 1024
THRESHOLD = 1e-10


def _build(seed: int):
    streams = np.random.SeedSequence(seed).spawn(3)
    regions = build_warped_voronoi_field(
        32,
        rng=np.random.default_rng(streams[0]),
        noise_seed=seed + 3000,
        noise_config=NOISE,
        warp_config=WARP,
    )
    angular = generate_plate_motion(
        regions.voronoi.seeds,
        PlateMotionConfig(),
        rng=np.random.default_rng(streams[2]),
    )
    regions_field = RegionInfluenceField(
        regions.voronoi,
        RegionInfluenceConfig(transition_half_width=TRANSITION_HALF_WIDTH),
    )
    overlap = RegionOverlapField(regions_field)
    rotations = RegionRotationField(regions.voronoi, angular)
    vectors = BoundaryVectorField(
        overlap, lambda positions, ids: rotations.sample_regions(positions, ids)
    )
    motion = BoundaryMotionField(vectors)
    interactions = BoundaryInteractionField(motion)

    def response(positions, sample):
        result = np.empty(len(sample.query_indices), dtype=np.float64)
        for i, (plane_distance, convergence, divergence, shear) in enumerate(
            zip(
                sample.plane_distance,
                sample.convergence,
                sample.divergence,
                sample.shear,
                strict=True,
            )
        ):
            distance = abs(float(plane_distance))
            broad, crest = collision_profile(distance, PROFILE_WIDTH, 0.2)
            divergent = divergent_profile(distance, PROFILE_WIDTH, continental=True)
            shear_shape = fault_profile(distance, PROFILE_WIDTH)
            result[i] = sample.influence[i] * (
                convergence * (0.65 * broad + 0.35 * crest)
                + divergence * divergent
                + 0.15 * shear * shear_shape
            )
        return result

    source_response = BoundaryResponseField(motion, response)
    warped_response = WarpedScalarField(regions.warp.sample, source_response.sample)
    world = {
        "regions": regions,
        "regions_field": regions_field,
        "overlap": overlap,
        "motion": motion,
        "source_response": source_response,
        "warped_response": warped_response,
        "interaction": interactions,
        "rotations": rotations,
    }
    return world, angular


def _sample(world, positions, case_id):
    q = positions if case_id == "source" else world["regions"].warp.sample(positions)
    region_sample = world["regions_field"].sample(q)
    overlap_sample = world["overlap"].sample_from_regions(region_sample)
    ownership = region_sample.voronoi.owner_seed_id
    motion = world["motion"].sample_from_overlap(q, overlap_sample)
    influence = np.bincount(
        overlap_sample.query_indices,
        weights=overlap_sample.influence,
        minlength=len(q),
    )
    grouped = world["interaction"].sample_from_motion(len(q), motion)
    components = {name: getattr(grouped, name) for name in CHANNELS}
    elevation = world["source_response"].sample_from_motion(q, motion)
    # Signed opening is a comparison channel only; its two nonnegative parts remain separate.
    opening = components["divergence"] - components["convergence"]
    return {
        "ownership": ownership,
        "influence": influence,
        **components,
        "opening": opening,
        "elevation": elevation,
    }


def _scalar_png(values, ownership, resolution, path, title, limits, cmap, label):
    fig, ax = plt.subplots(figsize=(10, 9), layout="constrained")
    image = ax.imshow(
        values.reshape(resolution, resolution),
        origin="lower",
        extent=(-1, 1, -1, 1),
        cmap=cmap,
        vmin=limits[0],
        vmax=limits[1],
        interpolation="nearest",
    )
    _draw_owner_outlines(ax, ownership, resolution)
    ax.set(title=title, xlabel="x", ylabel="y", aspect="equal")
    bar = fig.colorbar(image, ax=ax, orientation="horizontal", pad=0.08)
    bar.set_label(label)
    fig.savefig(path, dpi=100)
    plt.close(fig)


def _statistics(values):
    values = np.asarray(values, dtype=np.float64)
    if not len(values):
        return {
            "count": 0,
            **{
                key: None
                for key in (
                    "mean",
                    "rms",
                    "p10",
                    "p50",
                    "p90",
                    "p99",
                    "max",
                    "nonzero_fraction",
                )
            },
        }
    return {
        "count": int(len(values)),
        "mean": float(np.mean(values)),
        "rms": float(np.sqrt(np.mean(values**2))),
        "p10": float(np.percentile(values, 10)),
        "p50": float(np.percentile(values, 50)),
        "p90": float(np.percentile(values, 90)),
        "p99": float(np.percentile(values, 99)),
        "max": float(np.max(values)),
        "nonzero_fraction": float(np.mean(values > THRESHOLD)),
    }


def _distributions(world, points, case_id):
    q = points if case_id == "source" else world["regions"].warp.sample(points)
    region_sample = world["regions_field"].sample(q)
    overlap = world["overlap"].sample_from_regions(region_sample)
    active = np.zeros(len(q), dtype=bool)
    active[overlap.query_indices] = True
    raw = world["motion"].sample_from_overlap(q, overlap)
    grouped = world["interaction"].sample_from_motion(len(q), raw)
    pair_channels = {name: getattr(raw, name) for name in CHANNELS}
    grouped_channels = {name: getattr(grouped, name) for name in CHANNELS}
    total = (
        grouped_channels["convergence"]
        + grouped_channels["divergence"]
        + grouped_channels["shear"]
    )
    active_motion = active & (total > THRESHOLD)
    active_n = int(active.sum())
    dominant = grouped_channels["shear"] > (
        grouped_channels["convergence"] + grouped_channels["divergence"]
    )
    both = (grouped_channels["convergence"] > THRESHOLD) & (
        grouped_channels["divergence"] > THRESHOLD
    )
    return {
        "probe_count": len(q),
        "active_count": active_n,
        "active_fraction": float(active_n / len(q)) if len(q) else None,
        "zero_motion_count": int(np.count_nonzero((total <= THRESHOLD) & active)),
        "shear_dominant_fraction": float(np.mean(dominant[active_motion]))
        if np.any(active_motion)
        else None,
        "both_normal_fraction": float(np.mean(both[active])) if active_n else None,
        "channels": {
            name: {
                "all": _statistics(grouped_channels[name]),
                "active": _statistics(grouped_channels[name][active]),
            }
            for name in CHANNELS
        },
        "raw_pair_channels": {
            name: _statistics(pair_channels[name]) for name in CHANNELS
        },
    }


def _pole_diagnostics(world):
    regions_field = world["regions_field"]
    omega = world["rotations"].angular_velocity
    seeds = world["regions"].voronoi.seeds
    entries, alignments, stationary = [], [], 0
    for (first, second), normal in zip(
        regions_field.region_pairs, regions_field.pair_normals, strict=True
    ):
        first, second = int(first), int(second)
        delta = omega[second] - omega[first]
        norm = float(np.linalg.norm(delta))
        alignment = None if norm == 0 else float(abs(np.dot(delta, normal)) / norm)
        stationary += norm == 0
        if alignment is not None:
            alignments.append(alignment)
        entries.append(
            {
                "seed_pair": [first, second],
                "angular_difference_norm": norm,
                "normal_alignment": alignment,
                "coefficient_difference": float(
                    np.linalg.norm(omega[second]) / np.linalg.norm(seeds[second])
                    - np.linalg.norm(omega[first]) / np.linalg.norm(seeds[first])
                ),
            }
        )
    return {
        "normal_source": "all candidate seed-bisector normals, not physical adjacency",
        "pairs": entries,
        "stationary_pair_count": int(stationary),
        "alignment_quantiles": {
            f"p{p}": float(np.percentile(alignments, p)) if alignments else None
            for p in (50, 90, 99)
        },
    }


def _limits(samples):
    maxima = {name: 0.0 for name in ("influence", "convergence", "divergence", "shear")}
    elevation_max = 0.0
    for entry in samples:
        for surface in ("slice", "sphere"):
            for case in ("source", "warped"):
                data = entry[f"{surface}_{case}"]
                for name in maxima:
                    maxima[name] = max(
                        maxima[name], float(np.max(data[name], initial=0.0))
                    )
                elevation_max = max(
                    elevation_max, float(np.max(np.abs(data["elevation"]), initial=0.0))
                )
    return {
        "influence": [0.0, 1.0],
        "convergence": [0.0, max(maxima["convergence"], maxima["divergence"])],
        "divergence": [0.0, max(maxima["convergence"], maxima["divergence"])],
        "shear": [0.0, maxima["shear"]],
        "elevation": [-elevation_max, elevation_max],
    }, elevation_max


def _render_slice(data, resolution, seed, case_id, output, limits):
    palette = _palette()
    for layer in ("influence", *CHANNELS, "elevation"):
        cmap = (
            "viridis"
            if layer == "influence"
            else "BrBG_r"
            if layer == "elevation"
            else "magma"
        )
        label = (
            "Dimensionless diagnostic relief" if layer == "elevation" else layer.title()
        )
        _scalar_png(
            data[layer],
            data["ownership"],
            resolution,
            output / f"source-{seed}-{case_id}-{layer}.png",
            f"{case_id.title()} · {layer.title()}",
            limits[layer],
            cmap,
            label,
        )
    _render_ownership(
        data["ownership"],
        resolution,
        output / f"source-{seed}-{case_id}-ownership.png",
        palette,
        title=f"{case_id.title()} · Region ownership",
    )


def run(output, frequency, resolution):
    globe_errors = []
    output.mkdir(parents=True, exist_ok=True)
    sphere, faces = generate_icosphere(frequency)
    slice_points = _regular_xy_points(resolution)
    volume_points = np.random.default_rng(812).uniform(-1.0, 1.0, (32768, 3))
    started = perf_counter()
    worlds, manifest_worlds = [], []
    for seed in SEEDS:
        world, angular = _build(seed)
        print(
            f"[{seed}] Sampling {len(slice_points):,} slice, {len(sphere):,} sphere, and {len(volume_points):,} volume points",
            flush=True,
        )
        surfaces = {}
        for case_id, _ in CASES:
            for surface, points in (
                ("slice", slice_points),
                ("sphere", sphere),
                ("volume", volume_points),
            ):
                data = _sample(world, points, case_id)
                surfaces[f"{surface}_{case_id}"] = data
            dist = _distributions(world, volume_points, case_id)
            print(
                f"[{seed} {case_id}] volumetric distributions: "
                + json.dumps(dist, sort_keys=True),
                flush=True,
            )
            surfaces[f"distributions_{case_id}"] = dist
        pole_bias = _pole_diagnostics(world)
        print(
            f"[{seed}] seed-pole/candidate seed-bisector alignment: "
            + json.dumps(
                {
                    "stationary_pair_count": pole_bias["stationary_pair_count"],
                    "alignment_quantiles": pole_bias["alignment_quantiles"],
                },
                sort_keys=True,
            ),
            flush=True,
        )
        worlds.append(
            {
                "seed": seed,
                "world": world,
                "angular": angular,
                "surfaces": surfaces,
                "pole_bias_diagnostics": pole_bias,
            }
        )
    limits, elevation_max = _limits([w["surfaces"] for w in worlds])
    radial = 0.06 / elevation_max if elevation_max else 0.0
    rendering_started = perf_counter()
    manifest_worlds = []
    for entry in worlds:
        seed, world, surfaces = entry["seed"], entry["world"], entry["surfaces"]
        cases = []
        arrays = {
            "seeds": world["regions"].voronoi.seeds,
            "angular_velocity": entry["angular"],
            "slice_points": slice_points,
            "sphere_points": sphere,
            "volume_points": volume_points,
        }
        for case_id, title in CASES:
            images = {layer: f"source-{seed}-{case_id}-{layer}.png" for layer in LAYERS}
            print(f"[{seed} {case_id}] Rendering slice and globe", flush=True)
            _render_slice(
                surfaces[f"slice_{case_id}"], resolution, seed, case_id, output, limits
            )
            # Shared-scale globe rendering: retain numerical/slice assets on per-globe failure.
            globe_path = output / images["globe"]
            try:
                _render_globe(
                    sphere,
                    faces,
                    surfaces[f"sphere_{case_id}"]["elevation"],
                    globe_path,
                    limits=tuple(limits["elevation"]),
                    radial_factor=radial,
                )
            except Exception as error:
                globe_path.unlink(missing_ok=True)
                images["globe"] = None
                globe_errors.append(
                    {"seed": seed, "case_id": case_id, "error": str(error)}
                )
                print(f"[{seed} {case_id}] Globe render failed: {error}", flush=True)
            for surface in ("slice", "sphere", "volume"):
                data = surfaces[f"{surface}_{case_id}"]
                for field in (
                    "ownership",
                    "influence",
                    *CHANNELS,
                    "opening",
                    "elevation",
                ):
                    arrays[f"{case_id}_{surface}_{field}"] = data[field]
            metrics = {
                surface: {
                    name: _metrics(surfaces[f"{surface}_{case_id}"][name])
                    for name in ("influence", *CHANNELS, "elevation")
                }
                for surface in ("slice", "sphere", "volume")
            }
            cases.append(
                {
                    "id": case_id,
                    "title": title,
                    "images": images,
                    "metrics": metrics,
                    "distributions": surfaces[f"distributions_{case_id}"],
                }
            )
        np.savez(output / f"source-{seed}-fields.npz", **arrays)
        manifest_worlds.append(
            {
                "seed": seed,
                "fields_file": f"source-{seed}-fields.npz",
                "cases": cases,
                "pole_bias_diagnostics": entry["pole_bias_diagnostics"],
            }
        )
    manifest = {
        "settings": {
            "noise": {
                "octaves": 3,
                "base_frequency": 1.2,
                "lacunarity": 2.0,
                "persistence": 0.5,
            },
            "warp": {
                "iterations": 4,
                "amplitude": 0.24,
                "lacunarity": 1.7,
                "gain": 0.65,
            },
            "profile_recipe": {
                "collision_weights": [0.65, 0.35],
                "collision_crest_fraction": 0.2,
                "divergent_profile": "continental",
                "shear_coefficient": 0.15,
            },
            "transition_half_width_source": TRANSITION_HALF_WIDTH,
            "profile_width_source": PROFILE_WIDTH,
            "seed_count": 32,
            "slice_resolution": resolution,
            "frequency": frequency,
            "radial_factor": radial,
            "scalar_limits": limits,
            "distribution_zero_threshold": THRESHOLD,
            "volume_probe_seed": 812,
            "volume_probe_count": 32768,
        },
        "worlds": manifest_worlds,
        "timings_seconds": {
            "calculation": rendering_started - started,
            "render": perf_counter() - rendering_started,
        },
        "globe_render_errors": globe_errors,
    }
    (output / "source-deformation-results.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    template = Path(__file__).with_name("source_deformation.html")
    (output / "source-deformation.html").write_text(
        template.read_text(encoding="utf-8"), encoding="utf-8"
    )
    _publish_index(output, manifest)
    print(f"Completed source-space gallery at {output}", flush=True)


def _metrics(values):
    return {
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "rms": float(np.sqrt(np.mean(np.asarray(values, dtype=np.float64) ** 2))),
    }


def _publish_index(output, manifest):
    index = output / "index.html"
    if not index.exists():
        return
    text = index.read_text(encoding="utf-8")
    markers = (
        "<h1>Source-space local deformation</h1>",
        "<h1>Motion spaces: warp motion or warp relief?</h1>",
    )
    for marker in markers:
        marker_position = text.find(marker)
        if marker_position >= 0:
            start = text.rfind("<section", 0, marker_position)
            end = text.find("</section>", marker_position) + len("</section>")
            text = text[:start] + text[end:]

    main = text.find("<main")
    point = text.find(">", main) + 1
    source = manifest["worlds"][1]["cases"][1]
    image = source["images"]["globe"] or source["images"]["elevation"]
    note = (
        ""
        if source["images"]["globe"]
        else "<p>Globe rendering failed; showing the available elevation slice.</p>"
    )
    source_section = (
        "<section><h1>Source-space regional interactions</h1>"
        '<p><a href="source-deformation.html">Open diagnostic gallery</a></p>'
        f'{note}<img src="{image}" alt="Seed 2026 warped scalar response"></section>'
    )
    motion_image = output / "motion-2026-warped-scalar-globe.png"
    motion_preview = (
        f'<img src="{motion_image.name}" alt="Seed 2026 scalar-warp relief">'
        if motion_image.exists()
        else ""
    )
    motion_section = (
        "<section><h1>Source fields and scalar warp composition</h1>"
        "<p>Compare volumetric regional interactions at source coordinates with "
        "their scalar fields sampled through the warp.</p>"
        '<p><a href="motion-space.html">Open composition diagnostics</a></p>'
        f"{motion_preview}</section>"
    )
    text = text[:point] + source_section + motion_section + text[point:]
    index.write_text(text, encoding="utf-8")


def check():
    # Analytical affine and identity checks plus deterministic real field queries.
    from src.worldgen.field.compose import WarpedScalarField
    from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField

    points = np.array([[-1.0, 1.0, 0.0], [-0.75, 1.0, 0.0], [-0.5, 1.0, 0.0]])

    def affine(plane, iteration, axis, frequency_multiplier):
        return plane[:, 0] if axis == 0 else np.zeros(len(plane))

    warp = ShearWarpField(
        ShearWarpConfig(iterations=1, amplitude=1.0, lacunarity=1.0, gain=1.0),
        affine,
    )
    mapped = warp.sample(points)
    np.testing.assert_allclose(
        mapped,
        [[0.0, 1.0, 0.0], [0.25, 1.0, 0.0], [0.5, 1.0, 0.0]],
        atol=1e-12,
        rtol=0.0,
    )
    identity = WarpedScalarField(lambda x: x, lambda x: np.sum(x * 0.0, axis=1))
    probes = np.random.default_rng(812).uniform(-1, 1, (1307, 3))
    np.testing.assert_array_equal(identity.sample(probes), np.zeros(len(probes)))
    world, _ = _build(123)
    first = world["warped_response"].sample(probes[:16])
    second = world["warped_response"].sample(probes[:16])
    np.testing.assert_array_equal(first, second)
    print(
        "--check: affine coordinate mapping, identity scalar composition, and deterministic source/warped probes passed",
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("/tmp/domain-warp-voronoi-site")
    )
    parser.add_argument("--frequency", type=int, default=80)
    parser.add_argument("--slice-resolution", type=int, default=320)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check()
    else:
        run(args.output, args.frequency, args.slice_resolution)


if __name__ == "__main__":
    main()
