"""Render matched continuous elevation and crust examples for the web gallery."""

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.elevation.config import REFERENCE_RADIUS_M, TerrainVariationConfig
from src.worldgen.generate import generate_world
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.render.viewer import WorldgenViewer

SEEDS = (123, 2026, 31415)
LAYERS = (
    (
        "crust",
        "crust",
        "Categorical crust labels",
        "Discrete continental/oceanic identity at the hex samples.",
        False,
    ),
    (
        "continental-weight",
        "continental-weight",
        "Continental influence field",
        "A continuous scalar from 0 to 1; oceanic influence is its complement.",
        True,
    ),
    (
        "continental-weight-hex",
        "continental-weight",
        "Continental influence at hex centers",
        "The same material field sampled only at hex centers.",
        False,
    ),
    (
        "subduction-preference-strength",
        "subduction-preference-strength",
        "Subduction preference magnitude",
        "Magnitude of the separate seed-derived crust preference vector.",
        True,
    ),
    (
        "coastal-elevation",
        "coastal-elevation",
        "Coastal elevation",
        "Coastal profile sampled from continental influence, before tectonic relief.",
        True,
    ),
    (
        "terrain-variation",
        "terrain-variation",
        "General terrain variation",
        "Weak zero-centered noise evaluated in world XYZ after geological warping.",
        True,
    ),
    (
        "elevation",
        "elevation",
        "Composed elevation · variation on",
        "Coastal relief, tectonic response, and global terrain variation.",
        True,
    ),
    (
        "elevation-no-variation",
        "elevation",
        "Composed elevation · variation off",
        "Matched same-seed elevation with shared colors and variation disabled.",
        True,
    ),
)


def _elevation_range(
    worlds, field_frequency: int, radius_m: float
) -> tuple[float, float]:
    dense_positions, _ = generate_icosphere(field_frequency)
    arrays = []
    for world in worlds:
        dense = world.field.sample_world(dense_positions).elevation
        for result in (world.elevation, dense):
            arrays.extend((result.elevation, result.coastal_elevation))
    heights = np.concatenate(arrays) * radius_m
    low = min(float(np.min(heights, initial=0.0)), 0.0)
    high = max(float(np.max(heights, initial=0.0)), 0.0)
    return (-1e-12, 1e-12) if low == high else (low, high)


def render(
    output: Path,
    frequency: int,
    field_frequency: int,
    *,
    radius_m: float = REFERENCE_RADIUS_M,
    vertical_exaggeration: float = 100.0,
    variation_percent: float = TerrainVariationConfig().amplitude_percent,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    base = WorldgenConfig(subdivision_frequency=frequency)
    configured_config = replace(
        base,
        planet=replace(base.planet, radius_m=radius_m),
        elevation=replace(
            base.elevation,
            variation=TerrainVariationConfig(amplitude_percent=variation_percent),
        ),
    )
    zero_config = replace(
        configured_config,
        elevation=replace(
            configured_config.elevation,
            variation=TerrainVariationConfig(amplitude_percent=0.0),
        ),
    )

    worlds = []
    for seed in SEEDS:
        configured = generate_world(replace(configured_config, seed=seed))
        no_variation = generate_world(replace(zero_config, seed=seed))
        elevation_range = _elevation_range(
            (configured, no_variation), field_frequency, radius_m
        )
        viewer = WorldgenViewer(
            configured,
            field_frequency=field_frequency,
            off_screen=True,
            terrain_relief=True,
            vertical_exaggeration=vertical_exaggeration,
            elevation_range=elevation_range,
            continuous_field=True,
        )
        images = {}
        try:
            viewer.terrain_relief = True
            viewer.continuous_field = True
            viewer.elevation_range = elevation_range
            viewer.select_layer("elevation")
            viewer.prepare_camera()
            initial_camera = viewer.plotter.camera_position
            initial_parallel_scale = viewer.plotter.camera.parallel_scale
            for key, layer, _title, _description, continuous in LAYERS:
                if key == "elevation-no-variation":
                    continue
                viewer.set_continuous_field(continuous)
                viewer.select_layer(layer)
                filename = f"crust-material-{seed}-{key}.png"
                viewer.plotter.screenshot(str(output / filename))
                images[key] = filename
            viewer.set_continuous_field(True)
            viewer.select_layer("elevation")
            viewer.plotter.camera.Azimuth(180)
            viewer.plotter.render()
            opposite = f"crust-material-{seed}-elevation-opposite.png"
            viewer.plotter.screenshot(str(output / opposite))
            images["elevation-opposite"] = opposite
        finally:
            viewer.plotter.close()

        comparison = WorldgenViewer(
            no_variation,
            field_frequency=field_frequency,
            off_screen=True,
            terrain_relief=True,
            vertical_exaggeration=vertical_exaggeration,
            elevation_range=elevation_range,
            continuous_field=True,
        )
        try:
            comparison.select_layer("elevation")
            comparison.plotter.camera_position = initial_camera
            comparison.plotter.camera.parallel_projection = True
            comparison.plotter.camera.parallel_scale = initial_parallel_scale
            filename = f"crust-material-{seed}-elevation-no-variation.png"
            comparison.plotter.screenshot(str(output / filename))
            images["elevation-no-variation"] = filename
            comparison.plotter.camera.Azimuth(180)
            comparison.plotter.render()
            opposite = f"crust-material-{seed}-elevation-no-variation-opposite.png"
            comparison.plotter.screenshot(str(output / opposite))
            images["elevation-no-variation-opposite"] = opposite
        finally:
            comparison.plotter.close()

        worlds.append(
            {
                "seed": seed,
                "images": images,
                "elevation_range_m": list(elevation_range),
            }
        )
        print(f"Rendered crust field examples for seed {seed}", flush=True)

    coastal = configured_config.elevation.coastal
    manifest = {
        "title": "Crust material and continuous elevation",
        "frequency": frequency,
        "field_frequency": field_frequency,
        "radius_m": radius_m,
        "vertical_exaggeration": vertical_exaggeration,
        "terrain_variation_percent": variation_percent,
        "seeds": list(SEEDS),
        "coastal_profile": {
            "coastline_weight": coastal.coastline_weight,
            "inland_span": coastal.inland.span,
            "shelf_span": coastal.shelf.span,
            "slope_span": coastal.slope.span,
            "interior_height_percent": coastal.interior_height_percent,
            "shelf_depth_percent": coastal.shelf_depth_percent,
            "basin_depth_percent": coastal.basin_depth_percent,
        },
        "layers": [
            {"id": key, "title": title, "description": description}
            for key, _layer, title, description, _continuous in LAYERS
        ],
        "worlds": worlds,
    }
    (output / "crust-material-results.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    template = Path(__file__).with_name("crust_material_gallery.html")
    (output / "crust-material.html").write_text(
        template.read_text(encoding="utf-8"), encoding="utf-8"
    )
    _publish_index(output)
    print(f"Published crust material gallery at {output / 'crust-material.html'}")


def _publish_index(output: Path) -> None:
    index = output / "index.html"
    if not index.exists():
        return
    text = index.read_text(encoding="utf-8")
    start_marker = "<!-- crust-material-gallery:start -->"
    end_marker = "<!-- crust-material-gallery:end -->"
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    section = (
        f'{start_marker}\n<section id="crust-material-gallery">'
        "<h1>Crust material and continuous elevation</h1>"
        "<p>Compare crust influence, continuous elevation, and matched terrain-noise variants across three world seeds.</p>"
        '<p><a href="crust-material.html"><strong>Open the crust field gallery</strong></a></p>'
        '<a href="crust-material.html"><img src="crust-material-2026-elevation.png" alt="Composed elevation for world seed 2026"></a>'
        "</section>\n"
        f"{end_marker}\n"
    )
    if start >= 0 and end >= 0:
        end += len(end_marker)
        text = text[:start] + section + text[end:]
    else:
        text = text.replace("</body>", section + "</body>")
    index.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("/tmp/crust-material-gallery")
    )
    parser.add_argument("--frequency", type=int, default=20)
    parser.add_argument("--field-frequency", type=int, default=80)
    parser.add_argument("--radius-m", type=float, default=REFERENCE_RADIUS_M)
    parser.add_argument("--vertical-exaggeration", type=float, default=100.0)
    parser.add_argument(
        "--variation-percent",
        type=float,
        default=TerrainVariationConfig().amplitude_percent,
    )
    args = parser.parse_args()
    render(
        args.output,
        args.frequency,
        args.field_frequency,
        radius_m=args.radius_m,
        vertical_exaggeration=args.vertical_exaggeration,
        variation_percent=args.variation_percent,
    )


if __name__ == "__main__":
    main()
