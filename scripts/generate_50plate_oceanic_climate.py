#!/usr/bin/env python3
"""Generate complete climate layers for 50-plate 75% oceanic worlds."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ruff: noqa: E402
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from scripts.worldgen_render import Phase0World, Layer, rasterize_rgb
from src.worldgen.config.worldgen_config import WorldgenConfig, PlatesConfig
from src.worldgen.pipeline import WorldgenPipeline
from src.worldgen.bake import bake_to_grid, nearest_cell_per_tile, stamp_rivers


def generate_world_custom(
    size: int, seed: int, n_plates: int, continental_fraction: float, resolution: int | None = None
) -> Phase0World:
    """Generate a world with custom plate count and continental/oceanic ratio."""
    config = WorldgenConfig(
        seed=seed,
        size=size,
        plates=PlatesConfig(n_plates=n_plates, continental_fraction=continental_fraction),
    )

    _world, ctx = WorldgenPipeline(config=config).run_debug(seed=seed, size=size)

    render_size: int = resolution if resolution is not None else ctx.config.size
    nearest = nearest_cell_per_tile(geometry=ctx.geometry, size=render_size)
    grid = bake_to_grid(fields=ctx.fields, nearest=nearest)

    if ctx.rivers:
        stamp_rivers(
            grid=grid,
            rivers=ctx.rivers,
            geometry=ctx.geometry,
            fields=ctx.fields,
            size=render_size,
            cfg=ctx.config.river,
        )

    insolation = (
        ctx.fields.insolation[nearest]
        if ctx.fields.insolation is not None
        else np.zeros(nearest.shape[0], dtype=float)
    )

    return Phase0World(
        seed=seed,
        size=render_size,
        grid=grid,
        geometry=ctx.geometry,
        nearest=nearest,
        insolation=insolation,
    )


def add_plate_labels(image: Image.Image, world: Phase0World) -> Image.Image:
    """Add plate ID numbers to the plates layer visualization."""
    plate_ids = world.grid.plate_id.reshape(world.size, world.size)
    unique_plates = np.unique(plate_ids[plate_ids >= 0])

    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
    except OSError:
        font = ImageFont.load_default()

    for plate_id in unique_plates:
        plate_id = int(plate_id)
        mask = plate_ids == plate_id
        y_coords, x_coords = np.where(mask)

        if len(y_coords) > 0:
            center_x = int(np.mean(x_coords))
            center_y = int(np.mean(y_coords))

            img_x = center_x * 2
            img_y = center_y * 2

            text = str(plate_id)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            padding = 1
            draw.rectangle(
                [
                    (img_x - text_width // 2 - padding, img_y - text_height // 2 - padding),
                    (img_x + text_width // 2 + padding, img_y + text_height // 2 + padding),
                ],
                fill=(0, 0, 0, 180),
            )

            draw.text(
                (img_x - text_width // 2, img_y - text_height // 2),
                text,
                fill=(255, 255, 100),
                font=font,
            )

    return image


def export_all_layers(world: Phase0World, output_dir: Path, seed: int) -> None:
    """Export terrain and climate layers."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Terrain layers
    terrain_layers = [
        (Layer.ELEVATION, False),
        (Layer.PLATES, True),  # True = add plate labels
    ]

    # Climate layers
    climate_layers = [
        (Layer.LATITUDE, False),
        (Layer.INSOLATION, False),
        (Layer.TEMPERATURE, False),
        (Layer.SST, False),
        (Layer.WIND, False),
        (Layer.PRECIPITATION, False),
    ]

    all_layers = terrain_layers + climate_layers

    for layer, add_labels in all_layers:
        image = Image.fromarray(rasterize_rgb(world, layer), mode="RGB")
        image = image.resize((world.size * 2, world.size * 2), Image.Resampling.NEAREST)

        if add_labels:
            image = add_plate_labels(image, world)

        output_path = output_dir / f"{layer.value}.png"
        image.save(output_path)
        print(f"  ✓ {layer.value}.png")


def main() -> None:
    output_base = Path("output/50plate_75oceanic_climate")
    seeds = [301, 302, 303, 304, 305]
    size = 100
    resolution = 512
    n_plates = 50
    oceanic_fraction = 0.75
    continental_fraction = 1.0 - oceanic_fraction

    print(f"Generating complete climate data for {len(seeds)} worlds...\n")
    print(f"Layers per seed: elevation, plates, latitude, insolation, temperature, SST, wind, precipitation\n")

    for i, seed in enumerate(seeds, 1):
        seed_dir = output_base / f"seed_{seed}"
        print(f"[{i}/5] Seed {seed}:")

        world = generate_world_custom(
            size, seed, n_plates=n_plates, continental_fraction=continental_fraction, resolution=resolution
        )
        export_all_layers(world, seed_dir, seed)

    print(f"\n{'='*60}")
    print(f"✓ Generated complete climate data")
    print(f"{'='*60}")
    print(f"Seeds: {', '.join(str(s) for s in seeds)}")
    print(f"Layers per seed: 8 (terrain + climate)")
    print(f"Total images: {len(seeds) * 8} (5 seeds × 8 layers)")
    print(f"\nLayers generated:")
    print(f"  Terrain: elevation, plates (with IDs)")
    print(f"  Climate: latitude, insolation, temperature, SST, wind, precipitation")


if __name__ == "__main__":
    main()
