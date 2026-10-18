"""Temporary 3D domain-warped Voronoi experiment.

This file intentionally does not participate in ``src.worldgen``. It samples the
same OpenSimplex2S implementation used by the project, but builds an independent
Voronoi field in normalized cube coordinates and renders a static comparison page.
"""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
from matplotlib.colors import ListedColormap, hsv_to_rgb

from src.worldgen.field.noise import NoiseConfig, normalized_noise
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.geometry.mesh import Mesh


@dataclass(frozen=True, slots=True)
class WarpMode:
    name: str
    title: str
    iterations: int
    amplitude: float
    frequency: float
    lacunarity: float
    gain: float


MODES = (
    WarpMode("plain", "Unwarped Voronoi", 0, 0.0, 2.5, 1.8, 0.55),
    WarpMode("fractal-soft", "Fractal warp · soft", 4, 0.08, 2.0, 2.0, 0.55),
    WarpMode("fractal-current", "Fractal warp · current", 4, 0.14, 2.5, 1.8, 0.55),
    WarpMode("fractal-strong", "Fractal warp · strong", 4, 0.24, 2.5, 1.8, 0.55),
    WarpMode("fractal-fine", "Fractal warp · fine", 5, 0.10, 4.0, 2.0, 0.50),
    WarpMode("fractal-broad", "Fractal warp · broad", 3, 0.18, 1.2, 1.7, 0.65),
    WarpMode(
        "fractal-broad-strong",
        "Fractal warp · broad strong",
        4,
        0.24,
        1.2,
        1.7,
        0.65,
    ),
)


def _region_palette(seed_count: int) -> ListedColormap:
    """Return one stable, distinct hue for every Voronoi seed ID."""
    hues = (np.arange(seed_count, dtype=np.float64) * 0.61803398875) % 1.0
    hsv = np.column_stack((hues, np.full(seed_count, 0.68), np.full(seed_count, 0.9)))
    return ListedColormap(hsv_to_rgb(hsv), name=f"voronoi-{seed_count}")


def _signed_noise(
    positions: np.ndarray,
    *,
    seed: int,
    frequency: float,
    octaves: int = 3,
) -> np.ndarray:
    config = NoiseConfig(
        octaves=octaves,
        base_frequency=frequency,
        lacunarity=2.0,
        persistence=0.5,
    )
    return normalized_noise(positions, config, seed=seed) * 2.0 - 1.0


def domain_warp(
    positions: np.ndarray,
    *,
    seed: int,
    iterations: int,
    amplitude: float = 0.14,
    frequency: float = 2.5,
    lacunarity: float = 1.8,
    gain: float = 0.55,
) -> np.ndarray:
    """Apply nested vector fBm warps to normalized cube coordinates."""
    warped = np.asarray(positions, dtype=np.float64).copy()
    for iteration in range(iterations):
        iteration_frequency = frequency * lacunarity**iteration
        iteration_amplitude = amplitude * gain**iteration
        offsets = np.column_stack(
            (
                _signed_noise(
                    warped,
                    seed=seed + 1013 * iteration + 11,
                    frequency=iteration_frequency,
                ),
                _signed_noise(
                    warped,
                    seed=seed + 1013 * iteration + 37,
                    frequency=iteration_frequency,
                ),
                _signed_noise(
                    warped,
                    seed=seed + 1013 * iteration + 71,
                    frequency=iteration_frequency,
                ),
            )
        )
        warped += iteration_amplitude * offsets
    return warped


def sample_voronoi(
    positions: np.ndarray,
    seeds: np.ndarray,
    *,
    seed: int,
    iterations: int,
    amplitude: float,
    frequency: float,
    lacunarity: float,
    gain: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return nearest region, Voronoi edge gap, and edge display strength."""
    warped = domain_warp(
        positions,
        seed=seed,
        iterations=iterations,
        amplitude=amplitude,
        frequency=frequency,
        lacunarity=lacunarity,
        gain=gain,
    )
    distances_squared = np.sum(
        (warped[:, None, :] - seeds[None, :, :]) ** 2,
        axis=2,
    )
    nearest_two = np.partition(distances_squared, 1, axis=1)[:, :2]
    first = np.sqrt(np.min(nearest_two, axis=1))
    second = np.sqrt(np.max(nearest_two, axis=1))
    edge_gap = second - first
    edge_strength = np.exp(-edge_gap / 0.025)
    owners = np.argmin(distances_squared, axis=1)
    return owners, edge_gap, edge_strength


def _dual_polydata(mesh: Mesh) -> pv.PolyData:
    counts = [len(face) for face in mesh.dual_faces]
    cells = np.empty(sum(count + 1 for count in counts), dtype=np.int64)
    offset = 0
    for face in mesh.dual_faces:
        cells[offset] = len(face)
        cells[offset + 1 : offset + 1 + len(face)] = face
        offset += 1 + len(face)
    return pv.PolyData(mesh.dual_vertices, cells)


def _render_sphere(
    mesh: Mesh,
    owners: np.ndarray,
    edge_strength: np.ndarray,
    *,
    seed_count: int,
    region_palette: ListedColormap,
    title: str,
    output: Path,
    mode: str,
) -> None:
    polydata = _dual_polydata(mesh)
    values = owners if mode == "regions" else edge_strength
    scalar_name = "region" if mode == "regions" else "edge-strength"
    polydata.cell_data[scalar_name] = values
    plotter = pv.Plotter(off_screen=True, window_size=(800, 800))
    plotter.set_background("white")
    if mode == "regions":
        plotter.add_mesh(
            polydata,
            scalars=scalar_name,
            cmap=region_palette,
            clim=(0, seed_count - 1),
            categories=seed_count,
            show_edges=True,
            edge_color="black",
            line_width=0.25,
            scalar_bar_args={"title": "Voronoi region", "n_labels": 4},
        )
    else:
        plotter.add_mesh(
            polydata,
            scalars=scalar_name,
            cmap="magma",
            clim=(0.0, 1.0),
            show_edges=False,
            scalar_bar_args={"title": "Edge proximity", "n_labels": 4},
        )
    plotter.add_text(title, position="upper_left", font_size=14, color="black")
    plotter.view_isometric()
    plotter.camera.zoom(1.15)
    plotter.screenshot(output)
    plotter.close()


def _render_cube_slice(
    owners: np.ndarray,
    edge_strength: np.ndarray,
    *,
    resolution: int,
    seed_count: int,
    region_palette: ListedColormap,
    title: str,
    output: Path,
) -> None:
    owner_image = owners.reshape(resolution, resolution)
    edge_image = edge_strength.reshape(resolution, resolution)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    axes[0].imshow(
        owner_image,
        origin="lower",
        extent=(0.0, 1.0, 0.0, 1.0),
        interpolation="nearest",
        cmap=region_palette,
        vmin=0,
        vmax=seed_count - 1,
    )
    axes[0].set_title("Voronoi ownership at z = 0.5")
    axes[0].set_xlabel("x")
    axes[0].set_ylabel("y")
    image = axes[1].imshow(
        edge_image,
        origin="lower",
        extent=(0.0, 1.0, 0.0, 1.0),
        interpolation="bilinear",
        cmap="magma",
        vmin=0.0,
        vmax=1.0,
    )
    axes[1].contour(
        edge_image,
        levels=(0.55, 0.8, 0.95),
        extent=(0.0, 1.0, 0.0, 1.0),
        colors="white",
        linewidths=0.5,
    )
    axes[1].set_title("Continuous edge-proximity field")
    axes[1].set_xlabel("x")
    axes[1].set_ylabel("y")
    fig.colorbar(image, ax=axes[1], fraction=0.046, pad=0.04)
    fig.suptitle(title)
    fig.savefig(output, dpi=150)
    plt.close(fig)


def _write_index(
    output: Path,
    *,
    seed: int,
    mesh_frequency: int,
    seed_count: int,
    slice_resolution: int,
    metrics: list[dict[str, object]],
) -> None:
    cards = []
    for metric in metrics:
        cards.append(
            f"""
            <article class="card">
              <h2>{metric["title"]}</h2>
              <p>{metric["iterations"]} nested warp iteration(s), amplitude {metric["amplitude"]:.2f}, start frequency {metric["frequency"]:.2f}, lacunarity {metric["lacunarity"]:.2f}, gain {metric["gain"]:.2f}, {seed_count} Voronoi seeds.</p>
              <img src="{metric["cube_image"]}" alt="{metric["title"]} cube slice">
              <div class="pair">
                <figure><img src="{metric["sphere_regions"]}" alt="{metric["title"]} hex region samples"><figcaption>Hex-center region samples</figcaption></figure>
                <figure><img src="{metric["sphere_edges"]}" alt="{metric["title"]} hex edge-proximity samples"><figcaption>Hex-center edge proximity</figcaption></figure>
              </div>
              <dl>
                <dt>Sphere cells</dt><dd>{metric["cell_count"]}</dd>
                <dt>Observed regions</dt><dd>{metric["observed_regions"]}</dd>
                <dt>Edge-gap median</dt><dd>{metric["edge_gap_median"]:.5f}</dd>
                <dt>Edge-gap 95th percentile</dt><dd>{metric["edge_gap_p95"]:.5f}</dd>
              </dl>
            </article>
            """
        )
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Domain-warped 3D Voronoi experiment</title>
<style>
  :root {{ color-scheme: light; font-family: system-ui, sans-serif; }}
  body {{ margin: 0; background: #eef1f4; color: #18212b; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 1rem; }}
  h1 {{ margin-bottom: .4rem; }}
  .intro {{ background: white; border-radius: 14px; padding: 1rem 1.2rem; line-height: 1.45; }}
  .card {{ background: white; border-radius: 14px; padding: 1rem; margin-top: 1rem; box-shadow: 0 2px 10px #0001; }}
  img {{ display: block; width: 100%; height: auto; border-radius: 8px; }}
  .pair {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .75rem; margin-top: .75rem; }}
  figure {{ margin: 0; }}
  figcaption {{ text-align: center; font-size: .9rem; padding: .35rem; }}
  dl {{ display: grid; grid-template-columns: 1fr 1fr; gap: .25rem .8rem; max-width: 30rem; }}
  dt {{ font-weight: 650; }}
  dd {{ margin: 0; text-align: right; font-variant-numeric: tabular-nums; }}
  code {{ background: #e9edf1; padding: .1rem .25rem; border-radius: 4px; }}
  @media (max-width: 650px) {{ .pair {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body><main>
<section class="intro">
  <h1>Domain-warped 3D Voronoi experiment</h1>
  <p>This is isolated from <code>src/worldgen</code>. The field lives in normalized
  cube coordinates <code>[0,1]³</code>. A vector fBm warp is applied before a
  3D Voronoi lookup. The cube image samples a dense <code>z=0.5</code> slice;
  the globe images sample only the generated hex centers at frequency
  <code>{mesh_frequency}</code>.</p>
  <p>The edge view is the continuous Voronoi gap <code>F2-F1</code> converted to
  display brightness. Bright lines are close to a region boundary. The region
  view is categorical ownership sampled at the hex centers.</p>
  <p>The same fixed palette maps every Voronoi seed ID to the same colour in every
  comparison, even when a warp leaves some IDs unobserved on the sphere.</p>
  <p>Seed: <code>{seed}</code> · Voronoi seeds: <code>{seed_count}</code> · Cube slice:
  <code>{slice_resolution}×{slice_resolution}</code></p>
</section>
{"".join(cards)}
</main></body></html>
"""
    (output / "index.html").write_text(html, encoding="utf-8")
    (output / "results.json").write_text(
        json.dumps(
            {
                "seed": seed,
                "mesh_frequency": mesh_frequency,
                "seed_count": seed_count,
                "slice_resolution": slice_resolution,
                "modes": metrics,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def run(
    output: Path,
    *,
    seed: int,
    mesh_frequency: int,
    seed_count: int,
    slice_resolution: int,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    voronoi_seeds = rng.random((seed_count, 3))
    region_palette = _region_palette(seed_count)
    vertices, faces = generate_icosphere(mesh_frequency)
    mesh = Mesh(vertices, faces)
    sphere_positions = (mesh.vertices + 1.0) / 2.0
    axis = np.linspace(0.0, 1.0, slice_resolution, dtype=np.float64)
    grid_x, grid_y = np.meshgrid(axis, axis, indexing="xy")
    cube_slice = np.column_stack(
        (grid_x.ravel(), grid_y.ravel(), np.full(grid_x.size, 0.5))
    )

    metrics: list[dict[str, object]] = []
    for mode in MODES:
        cube_owners, _, cube_edge_strength = sample_voronoi(
            cube_slice,
            voronoi_seeds,
            seed=seed,
            iterations=mode.iterations,
            amplitude=mode.amplitude,
            frequency=mode.frequency,
            lacunarity=mode.lacunarity,
            gain=mode.gain,
        )
        sphere_owners, sphere_edge_gap, sphere_edge_strength = sample_voronoi(
            sphere_positions,
            voronoi_seeds,
            seed=seed,
            iterations=mode.iterations,
            amplitude=mode.amplitude,
            frequency=mode.frequency,
            lacunarity=mode.lacunarity,
            gain=mode.gain,
        )
        _render_cube_slice(
            cube_owners,
            cube_edge_strength,
            resolution=slice_resolution,
            seed_count=seed_count,
            region_palette=region_palette,
            title=mode.title,
            output=output / f"cube-{mode.name}.png",
        )
        _render_sphere(
            mesh,
            sphere_owners,
            sphere_edge_strength,
            seed_count=seed_count,
            region_palette=region_palette,
            title=f"{mode.title} · hex-center region samples",
            output=output / f"sphere-{mode.name}-regions.png",
            mode="regions",
        )
        _render_sphere(
            mesh,
            sphere_owners,
            sphere_edge_strength,
            seed_count=seed_count,
            title=f"{mode.title} · hex-center edge proximity",
            region_palette=region_palette,
            output=output / f"sphere-{mode.name}-edges.png",
            mode="edges",
        )
        metrics.append(
            {
                "name": mode.name,
                "title": mode.title,
                "iterations": mode.iterations,
                "amplitude": mode.amplitude,
                "frequency": mode.frequency,
                "lacunarity": mode.lacunarity,
                "gain": mode.gain,
                "cell_count": len(sphere_owners),
                "observed_regions": int(len(np.unique(sphere_owners))),
                "edge_gap_median": float(np.median(sphere_edge_gap)),
                "edge_gap_p95": float(np.percentile(sphere_edge_gap, 95.0)),
                "cube_image": f"cube-{mode.name}.png",
                "sphere_regions": f"sphere-{mode.name}-regions.png",
                "sphere_edges": f"sphere-{mode.name}-edges.png",
            }
        )
        print(
            f"{mode.name}: cells={len(sphere_owners)} "
            f"regions={len(np.unique(sphere_owners))} "
            f"edge_gap_median={np.median(sphere_edge_gap):.5f} "
            f"edge_gap_p95={np.percentile(sphere_edge_gap, 95.0):.5f}"
        )

    _write_index(
        output,
        seed=seed,
        mesh_frequency=mesh_frequency,
        seed_count=seed_count,
        slice_resolution=slice_resolution,
        metrics=metrics,
    )
    print(f"site: {output / 'index.html'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("/tmp/domain-warp-voronoi-site")
    )
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--frequency", type=int, default=20)
    parser.add_argument("--voronoi-seeds", type=int, default=32)
    parser.add_argument("--slice-resolution", type=int, default=180)
    args = parser.parse_args()
    run(
        args.output,
        seed=args.seed,
        mesh_frequency=args.frequency,
        seed_count=args.voronoi_seeds,
        slice_resolution=args.slice_resolution,
    )


if __name__ == "__main__":
    main()
