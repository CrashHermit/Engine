from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ruff: noqa: E402
from PIL import Image, ImageDraw

from scripts.worldgen_render import (
    GRID_COLOR,
    LAYER_ORDER,
    Layer,
    Phase0World,
    generate_world,
    rasterize_rgb,
)


def _overlay_grid_lines(image: Image.Image, size: int, scale: int) -> Image.Image:
    """Draw thin grid lines between tiles (only legible at scale >= ~4)."""
    canvas = ImageDraw.Draw(image)
    for i in range(size + 1):
        pos = i * scale
        canvas.line([(pos, 0), (pos, size * scale)], fill=GRID_COLOR, width=1)
        canvas.line([(0, pos), (size * scale, pos)], fill=GRID_COLOR, width=1)
    return image


def export_layer(
    world: Phase0World,
    layer: Layer,
    output: Path,
    scale: int,
    grid: bool,
) -> None:
    # Vectorized colorize → one numpy array → one PIL image (fast even at 2k+).
    image = Image.fromarray(rasterize_rgb(world, layer), mode="RGB")
    if scale > 1:
        image = image.resize(
            (world.size * scale, world.size * scale), Image.Resampling.NEAREST
        )
    if grid:
        image = _overlay_grid_lines(image, world.size, scale)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    print(f"Wrote {output} ({image.width}x{image.height}, layer={layer.value})")


def parse_args() -> argparse.Namespace:
    layer_names = [layer.value for layer in LAYER_ORDER]
    parser = argparse.ArgumentParser(description="Export worldgen maps to PNG.")
    parser.add_argument("--seed", type=int, default=0, help="World seed (default: 0)")
    parser.add_argument(
        "--size", type=int, default=200, help="Gameplay grid size (default: 200)"
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=None,
        help=(
            "Render resolution in tiles, decoupled from --size. Bakes the mesh "
            "directly at this resolution so PNGs resolve full mesh detail "
            "(e.g. --resolution 1024). Defaults to --size."
        ),
    )
    parser.add_argument(
        "--layer",
        choices=layer_names,
        default="elevation",
        help="Layer to export (default: elevation)",
    )
    parser.add_argument(
        "--all-layers",
        action="store_true",
        help="Export every layer into the output directory",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=4,
        help="Pixels per grid node (default: 4)",
    )
    parser.add_argument(
        "--grid",
        action="store_true",
        help="Draw grid lines between nodes",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output/worldgen.png"),
        help="Output PNG path (default: output/worldgen.png)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.scale < 1:
        raise SystemExit("--scale must be >= 1")

    if args.resolution is not None and args.resolution < 1:
        raise SystemExit("--resolution must be >= 1")

    detail = args.resolution if args.resolution is not None else args.size
    print(
        f"Generating world (seed={args.seed}, size={args.size}, "
        f"render={detail}x{detail})..."
    )
    world = generate_world(args.size, args.seed, resolution=args.resolution)

    if args.all_layers:
        out_dir = args.output if args.output.suffix == "" else args.output.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        for layer in LAYER_ORDER:
            path = out_dir / f"{layer.value}.png"
            export_layer(world, layer, path, args.scale, args.grid)
    else:
        layer = Layer(args.layer)
        export_layer(world, layer, args.output, args.scale, args.grid)


if __name__ == "__main__":
    main()
