#!/usr/bin/env python3
"""
Generate terrain layers for 10 seeds with plate numbers labeled.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ruff: noqa: E402
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from scripts.worldgen_render import (
    LAYER_ORDER,
    Layer,
    Phase0World,
    generate_world,
    rasterize_rgb,
)


def add_plate_labels(image: Image.Image, world: Phase0World) -> Image.Image:
    """Add plate ID numbers to the plates layer visualization."""
    plate_ids = world.grid.plate_id.reshape(world.size, world.size)
    unique_plates = np.unique(plate_ids[plate_ids >= 0])

    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except OSError:
        font = ImageFont.load_default()

    for plate_id in unique_plates:
        plate_id = int(plate_id)
        mask = plate_ids == plate_id
        y_coords, x_coords = np.where(mask)

        if len(y_coords) > 0:
            center_x = int(np.mean(x_coords))
            center_y = int(np.mean(y_coords))

            # Scale to image coordinates (2x scale)
            img_x = center_x * 2
            img_y = center_y * 2

            text = str(plate_id)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            padding = 3
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


def export_terrain_layers(
    world: Phase0World,
    output_dir: Path,
    seed: int,
) -> None:
    """Export just terrain layers for a seed."""
    output_dir.mkdir(parents=True, exist_ok=True)

    terrain_layers = [
        Layer.ELEVATION,
        Layer.PLATES,
        Layer.UPLIFT,
        Layer.DRAINAGE,
        Layer.VOLCANISM,
        Layer.LAND,
    ]

    for layer in terrain_layers:
        # Generate the base image
        image = Image.fromarray(rasterize_rgb(world, layer), mode="RGB")

        # Scale up for visibility
        scale = 2
        image = image.resize(
            (world.size * scale, world.size * scale), Image.Resampling.NEAREST
        )

        # Add plate numbers to plates layer
        if layer == Layer.PLATES:
            image = add_plate_labels(image, world)

        output_path = output_dir / f"{layer.value}.png"
        image.save(output_path)
        print(f"  ✓ {layer.value}.png ({image.width}x{image.height})")


def main() -> None:
    output_base = Path("output/terrain_seeds")
    seeds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    size = 100
    resolution = 512

    print(f"Generating terrain layers for {len(seeds)} seeds...\n")

    for i, seed in enumerate(seeds, 1):
        seed_dir = output_base / f"seed_{seed}"
        print(f"[{i}/10] Seed {seed}:")

        world = generate_world(size, seed, resolution=resolution)
        export_terrain_layers(world, seed_dir, seed)

    print(f"\n{'='*60}")
    print(f"✓ Generated terrain layers in {output_base}")
    print(f"{'='*60}")
    print(f"Seeds: {', '.join(str(s) for s in seeds)}")
    print(f"Layers per seed: elevation, plates (with numbers), uplift, drainage, volcanism, land")


if __name__ == "__main__":
    main()
