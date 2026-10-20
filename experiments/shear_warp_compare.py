"""Temporary, matched displacement-versus-invertible-shear comparison."""

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from src.worldgen.field.noise import NoiseConfig, sample_vector_noise
from src.worldgen.field.seeds import generate_seed_cloud
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.field.noise_warp import build_noise_shear_warp
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.geometry.mesh import Mesh


NOISE = NoiseConfig(octaves=3, base_frequency=1.2, lacunarity=2.0, persistence=0.5)
ITERATIONS = 4
LACUNARITY = 1.7
GAIN = 0.65
CHANNELS = (11, 37, 71)
CASES = (
    ("plain", "Unwarped reference", 0.0),
    ("displacement-broad", "Displacement — broad", 0.24),
    ("shear-broad", "Invertible shears — broad", 0.24),
    ("displacement-strong", "Displacement — strong", 0.48),
    ("shear-strong", "Invertible shears — strong", 0.48),
)


def octave_noise(iteration: int) -> NoiseConfig:
    return replace(NOISE, base_frequency=NOISE.base_frequency * LACUNARITY**iteration)


@dataclass(frozen=True, slots=True)
class DisplacementWarp:
    """Historical simultaneous displacement retained only for comparison."""

    amplitude: float
    seed: int

    def sample(self, positions: np.ndarray) -> np.ndarray:
        warped = np.array(positions, dtype=np.float64, copy=True)
        if len(warped) == 0 or self.amplitude == 0.0:
            return warped

        for iteration in range(ITERATIONS):
            offsets = sample_vector_noise(
                warped,
                octave_noise(iteration),
                seeds=tuple(
                    self.seed + 1013 * iteration + channel for channel in CHANNELS
                ),
            )
            warped += self.amplitude * GAIN**iteration * offsets
        return warped


def shear_warp(amplitude: float, seed: int) -> ShearWarpField:
    return build_noise_shear_warp(
        NOISE,
        ShearWarpConfig(
            iterations=ITERATIONS,
            amplitude=amplitude,
            lacunarity=LACUNARITY,
            gain=GAIN,
        ),
        seed=seed,
    )


def diagnose(warp, points: np.ndarray) -> dict:
    step = 1e-3
    jacobian = np.empty((len(points), 3, 3))
    for axis in range(3):
        offset = np.zeros(3)
        offset[axis] = step
        jacobian[:, :, axis] = (
            warp.sample(points + offset) - warp.sample(points - offset)
        ) / (2.0 * step)
    determinant = np.linalg.det(jacobian)
    roundtrip_error = None
    if isinstance(warp, ShearWarpField):
        restored = warp.inverse(warp.sample(points))
        roundtrip_error = float(np.max(np.abs(restored - points)))
        np.testing.assert_allclose(restored, points, atol=1e-4, rtol=0.0)
    return {
        "sample_count": len(points),
        "finite_difference_step": step,
        "min_determinant": float(determinant.min()),
        "max_determinant": float(determinant.max()),
        "negative_determinant_fraction": float(np.mean(determinant < 0.0)),
        "roundtrip_max_error": roundtrip_error,
    }


def surface_metrics(mesh: Mesh, owners: np.ndarray) -> tuple[int, int]:
    same = owners[mesh.edges[:, 0]] == owners[mesh.edges[:, 1]]
    edges = mesh.edges[same]
    graph = coo_matrix(
        (np.ones(len(edges)), (edges[:, 0], edges[:, 1])),
        shape=(len(owners), len(owners)),
    ).tocsr()
    _, patches = connected_components(graph, directed=False)
    _, first = np.unique(patches, return_index=True)
    counts = np.bincount(owners[first], minlength=int(owners.max()) + 1)
    return len(np.unique(owners)), int(np.count_nonzero(counts > 1))


def dual_polydata(mesh: Mesh) -> pv.PolyData:
    cells = np.concatenate(
        [np.asarray([len(face), *face], dtype=np.int64) for face in mesh.dual_faces]
    )
    return pv.PolyData(mesh.dual_vertices, cells)


def globe_image(polydata: pv.PolyData, colors: np.ndarray, output: Path) -> None:
    plotter = pv.Plotter(off_screen=True, shape=(1, 2), window_size=(1400, 700))
    polydata.cell_data["colors"] = colors
    directions = ((1.6, -2.4, 1.2), (-1.8, 1.6, -0.6))
    for column, direction in enumerate(directions):
        plotter.subplot(0, column)
        plotter.set_background("#f4f6f8")
        plotter.add_mesh(
            polydata,
            scalars="colors",
            rgb=True,
            show_scalar_bar=False,
            ambient=0.65,
            diffuse=0.35,
            specular=0.0,
        )
        plotter.camera_position = (direction, (0, 0, 0), (0, 0, 1))
        plotter.enable_parallel_projection()
        plotter.camera.parallel_scale = 1.1
        plotter.add_text(f"View {'AB'[column]}", font_size=13, color="#18212b")
    plotter.screenshot(str(output))
    plotter.close()


def slice_image(plate_colors, crust_colors, output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), layout="constrained")
    for axis, colors, title in zip(
        axes,
        (plate_colors, crust_colors),
        ("Plate ownership", "Crust material"),
        strict=True,
    ):
        axis.imshow(
            colors.reshape((320, 320, 3)), origin="lower", extent=(-1, 1, -1, 1)
        )
        axis.set(title=title, xlabel="x", ylabel="y", aspect="equal")
    fig.suptitle("Same full 3D fields, queried on z = 0")
    fig.savefig(output, dpi=130)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("/tmp/domain-warp-voronoi-site")
    )
    parser.add_argument("--frequency", type=int, default=80)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    vertices, faces = generate_icosphere(args.frequency)
    mesh = Mesh(vertices, faces)
    polydata = dual_polydata(mesh)
    palette = np.asarray(plt.get_cmap("gist_ncar")(np.linspace(0.05, 0.95, 32))[:, :3])
    palette = np.rint(palette * 255).astype(np.uint8)
    material_palette = np.array([[39, 107, 153], [193, 161, 108]], dtype=np.uint8)
    axis = np.linspace(-1, 1, 320)
    x, y = np.meshgrid(axis, axis)
    slice_points = np.column_stack((x.ravel(), y.ravel(), np.zeros(x.size)))
    probe = np.random.default_rng(812).uniform(-1, 1, (1024, 3))
    result = {
        "frequency": args.frequency,
        "cell_count": len(vertices),
        "plate_seed_count": 32,
        "crust_seed_count": 24,
        "continental_seed_count": 6,
        "settings": {
            "noise_octaves": NOISE.octaves,
            "frequency": NOISE.base_frequency,
            "noise_lacunarity": NOISE.lacunarity,
            "noise_persistence": NOISE.persistence,
            "warp_iterations": ITERATIONS,
            "warp_lacunarity": LACUNARITY,
            "warp_gain": GAIN,
        },
        "worlds": [],
    }
    for seed in (123, 2026, 31415):
        streams = np.random.SeedSequence(seed).spawn(3)
        plate_field = VoronoiField3D(
            generate_seed_cloud(32, rng=np.random.default_rng(streams[0]))
        )
        crust_field = VoronoiField3D(
            generate_seed_cloud(24, rng=np.random.default_rng(streams[1]))
        )
        continental = np.zeros(24, dtype=np.int64)
        continental[np.random.default_rng(streams[2]).choice(24, 6, replace=False)] = 1
        world = {"seed": seed, "cases": []}
        for case_id, title, amplitude in CASES:
            started = perf_counter()
            make_warp = shear_warp if case_id.startswith("shear") else DisplacementWarp
            plate_warp = make_warp(amplitude, seed + 3000)
            crust_warp = make_warp(amplitude, seed + 6000)
            warped_vertices = plate_warp.sample(vertices)
            plate_ids = plate_field.sample(warped_vertices).owner_seed_id
            crust_ids = crust_field.sample(crust_warp.sample(vertices)).owner_seed_id
            # Arbitrary-position evaluation must not depend on the surrounding batch.
            np.testing.assert_array_equal(
                plate_warp.sample(vertices[::1001]), warped_vertices[::1001]
            )
            pcount, pdisconnected = surface_metrics(mesh, plate_ids)
            ccount, cdisconnected = surface_metrics(mesh, crust_ids)
            images = {
                kind: f"shear-{seed}-{case_id}-{kind}.png"
                for kind in ("plates", "crust", "slice")
            }
            globe_image(polydata, palette[plate_ids], args.output / images["plates"])
            globe_image(
                polydata,
                material_palette[continental[crust_ids]],
                args.output / images["crust"],
            )
            slice_plates = plate_field.sample(
                plate_warp.sample(slice_points)
            ).owner_seed_id
            slice_crust = crust_field.sample(
                crust_warp.sample(slice_points)
            ).owner_seed_id
            slice_image(
                palette[slice_plates],
                material_palette[continental[slice_crust]],
                args.output / images["slice"],
            )
            diagnostics = diagnose(plate_warp, probe)
            row = {
                "id": case_id,
                "title": title,
                "amplitude": amplitude,
                "images": images,
                "metrics": {
                    "plate_regions": pcount,
                    "plate_regions_with_multiple_patches": pdisconnected,
                    "crust_regions": ccount,
                    "crust_regions_with_multiple_patches": cdisconnected,
                    "continental_cell_fraction": float(np.mean(continental[crust_ids])),
                },
                "diagnostics": diagnostics,
            }
            world["cases"].append(row)
            print(
                json.dumps(
                    {
                        "seed": seed,
                        "case": case_id,
                        "elapsed_s": round(perf_counter() - started, 2),
                        **row["metrics"],
                        **diagnostics,
                    }
                ),
                flush=True,
            )
        result["worlds"].append(world)
    (args.output / "shear-warp-results.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(f"Published data and images to {args.output}", flush=True)


if __name__ == "__main__":
    main()
