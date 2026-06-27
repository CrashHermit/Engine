from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Imports after sys.path setup so `src` resolves when run as a script.
# ruff: noqa: E402
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.color import Color
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Footer, Header, Static
from textual_canvas import Canvas

from scripts.export_worldgen import export_layer
from scripts.worldgen_render import (
    LAYER_DESCRIPTIONS,
    LAYER_GROUPS,
    LAYER_LABELS,
    LAYER_ORDER,
    Layer,
    Phase0World,
    generate_world,
    rasterize_display,
)

# Re-export for backwards compatibility if anything imported from view_worldgen
__all__ = ["Layer", "Phase0World", "generate_world", "rasterize_display"]

MIN_VIEW_SIZE: int = 24
DEFAULT_VIEW_SIZE: int = 72
MAX_VIEW_SIZE: int = 120
DEFAULT_PNG_SCALE: int = 4


def default_view_size(grid_size: int) -> int:
    """Pick a canvas size that fits most terminals without downsampling huge worlds."""
    return min(grid_size, DEFAULT_VIEW_SIZE)


def clamp_view_size(view_size: int) -> int:
    """Clamp interactive view resolution to terminal-friendly bounds."""
    return max(MIN_VIEW_SIZE, min(view_size, MAX_VIEW_SIZE))


def draw_layer(
    canvas: Canvas,
    world: Phase0World,
    layer: Layer,
    display_size: int,
) -> None:
    """Paint the active layer onto the canvas at the given display resolution."""
    pixels = rasterize_display(world=world, layer=layer, display_size=display_size)
    with canvas.batch_refresh():
        canvas.clear()
        for rgb, locations in pixels.items():
            canvas.set_pixels(locations, Color(*rgb))


class WorldgenViewerApp(App[None]):
    TITLE = "Worldgen Viewer"
    CSS = """
    Screen {
        layout: vertical;
    }

    #sidebar {
        width: 30;
        height: 1fr;
        padding: 1;
        background: $panel;
        border-right: solid $accent;
    }

    #info-title {
        text-style: bold;
    }

    #info-desc {
        color: $text-muted;
        margin-bottom: 1;
    }

    #info-meta {
        color: $text-muted;
        margin-bottom: 1;
    }

    /* The layer list scrolls — the catalogue is longer than most terminals. */
    #layer-bar {
        height: 1fr;
        scrollbar-size-vertical: 1;
    }

    .group-header {
        text-style: bold;
        color: $accent;
        margin-top: 1;
    }

    #layer-bar Button {
        width: 100%;
    }

    #map-area {
        width: 1fr;
        height: 1fr;
        align: center middle;
    }

    Canvas {
        border: round $accent;
    }

    Footer {
        background: $panel;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "reroll", "Re-roll"),
        Binding("p", "export_png", "Save PNG"),
        Binding("equal", "zoom_in", "Zoom in", show=False),
        Binding("plus", "zoom_in", "Zoom in"),
        Binding("minus", "zoom_out", "Zoom out"),
        Binding("right_square_bracket", "next_layer", "Next layer", key_display="]"),
        Binding("left_square_bracket", "prev_layer", "Prev layer", key_display="["),
        Binding("j", "next_layer", "Next layer", show=False),
        Binding("k", "prev_layer", "Prev layer", show=False),
    ]

    def __init__(
        self,
        grid_size: int,
        seed: int,
        view_size: int,
        png_output_dir: Path,
        png_scale: int,
    ) -> None:
        super().__init__()
        self._grid_size: int = grid_size
        self._seed: int = seed
        self._view_size: int = view_size
        self._png_output_dir: Path = png_output_dir
        self._png_scale: int = png_scale
        self._layer: Layer = Layer.ELEVATION
        self._world_data: Phase0World | None = None
        self._canvas: Canvas | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("Layer", id="info-title")
                yield Static("", id="info-desc")
                yield Static("", id="info-meta")
                with VerticalScroll(id="layer-bar"):
                    for group_name, layers in LAYER_GROUPS:
                        yield Static(group_name, classes="group-header")
                        for layer in layers:
                            yield Button(
                                LAYER_LABELS[layer],
                                id=f"btn-{layer.value}",
                                variant="default",
                            )
            with Vertical(id="map-area"):
                self._canvas = Canvas(
                    MAX_VIEW_SIZE,
                    MAX_VIEW_SIZE,
                    Color(0, 0, 0),
                )
                yield self._canvas
        yield Footer()

    def on_mount(self) -> None:
        self._regenerate()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id and button_id.startswith("btn-"):
            self.action_layer(button_id.removeprefix("btn-"))


    def _tiles_per_pixel(self) -> float:
        """Average world tiles represented by each canvas pixel at the current zoom."""
        return self._grid_size / self._view_size

    def _update_ui(self) -> None:
        grid_label = f"{self._grid_size}x{self._grid_size}"
        view_label = f"{self._view_size}x{self._view_size}"
        zoom_label = (
            f"~{self._tiles_per_pixel():.1f} tiles/px"
            if self._tiles_per_pixel() > 1.05
            else "1:1"
        )
        self.sub_title = (
            f"seed {self._seed}  |  grid {grid_label}  |  view {view_label}  |  {zoom_label}"
        )
        position = LAYER_ORDER.index(self._layer) + 1
        self.query_one("#info-title", Static).update(
            f"{LAYER_LABELS[self._layer]}  ({position}/{len(LAYER_ORDER)})"
        )
        self.query_one("#info-desc", Static).update(LAYER_DESCRIPTIONS[self._layer])
        self.query_one("#info-meta", Static).update(
            "[ [ ] / [ ] ] cycle layers (or click)\n"
            "[+]/[-] zoom view  [p] full-res PNG\n"
            "[r] re-roll  [q] quit"
        )
        for layer in LAYER_ORDER:
            button = self.query_one(f"#btn-{layer.value}", Button)
            button.set_class(self._layer == layer, "-active")

    def _scroll_active_into_view(self) -> None:
        """Keep the selected layer's button visible when cycling by keyboard."""
        try:
            button = self.query_one(f"#btn-{self._layer.value}", Button)
        except Exception:
            return
        button.scroll_visible(animate=False)

    def _canvas_widget(self) -> Canvas:
        """Return the map canvas, whether stored on self or queried from the DOM."""
        if self._canvas is not None:
            return self._canvas
        map_area = self.query_one("#map-area", Vertical)
        return map_area.query_one(Canvas)

    def _redraw(self) -> None:
        """Redraw the current layer if world data is loaded."""
        if self._world_data is None:
            return
        draw_layer(
            canvas=self._canvas_widget(),
            world=self._world_data,
            layer=self._layer,
            display_size=self._view_size,
        )
        self._update_ui()

    def _regenerate(self) -> None:
        self._world_data = generate_world(self._grid_size, self._seed)
        self._redraw()

    def action_reroll(self) -> None:
        self._seed = random.randint(0, 2**31 - 1)
        self._regenerate()

    def action_layer(self, layer_name: str) -> None:
        self._layer = Layer(layer_name)
        self._redraw()
        self._scroll_active_into_view()

    def _step_layer(self, delta: int) -> None:
        """Move the active layer ``delta`` steps through LAYER_ORDER (wrapping)."""
        index = (LAYER_ORDER.index(self._layer) + delta) % len(LAYER_ORDER)
        self._layer = LAYER_ORDER[index]
        self._redraw()
        self._scroll_active_into_view()

    def action_next_layer(self) -> None:
        self._step_layer(1)

    def action_prev_layer(self) -> None:
        self._step_layer(-1)

    def action_zoom_in(self) -> None:
        """Increase sampling resolution (each pixel covers fewer world tiles)."""
        new_size: int = clamp_view_size(round(self._view_size * 1.25))
        if new_size == self._view_size:
            return
        self._view_size = new_size
        self._redraw()

    def action_zoom_out(self) -> None:
        """Decrease sampling resolution to see more of the world at once."""
        new_size: int = clamp_view_size(round(self._view_size * 0.8))
        if new_size == self._view_size:
            return
        self._view_size = new_size
        self._redraw()

    def action_export_png(self) -> None:
        """Write the current layer (full resolution) to the output directory."""
        if self._world_data is None:
            return
        self._png_output_dir.mkdir(parents=True, exist_ok=True)
        output_path: Path = (
            self._png_output_dir
            / f"seed{self._seed}_{self._layer.value}.png"
        )
        export_layer(
            world=self._world_data,
            layer=self._layer,
            output=output_path,
            scale=self._png_scale,
            grid=False,
        )
        self.notify(f"Saved {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="View worldgen pipeline output (TUI) or export PNGs.",
    )
    parser.add_argument("--seed", type=int, default=0, help="World seed (default: 0)")
    parser.add_argument(
        "--size",
        type=int,
        default=1000,
        help=(
            "World grid size in tiles (default: 1000, matching gameplay). "
            "Generation scales with size**2; 1000 hits the mesh cap and runs the "
            "full erosion loop, so a single world can take many minutes. Pass a "
            "smaller value (e.g. --size 160) for fast interactive browsing."
        ),
    )
    parser.add_argument(
        "--view-size",
        type=int,
        default=0,
        help=(
            "Initial view pixels per side (24-120); 0 = auto (default: min(size, 72))"
        ),
    )
    parser.add_argument(
        "--png-dir",
        type=Path,
        default=Path("output"),
        help="Directory for [p] key PNG exports (default: output/)",
    )
    parser.add_argument(
        "--png-scale",
        type=int,
        default=DEFAULT_PNG_SCALE,
        help="Pixels per grid tile in saved PNGs (default: 4)",
    )
    layer_names = [layer.value for layer in LAYER_ORDER]
    parser.add_argument(
        "--export",
        type=Path,
        metavar="PATH",
        help="Export one layer to PNG and exit (use with --layer)",
    )
    parser.add_argument(
        "--export-all",
        type=Path,
        metavar="DIR",
        help="Export every layer to PNG files in DIR and exit",
    )
    parser.add_argument(
        "--layer",
        choices=layer_names,
        default="elevation",
        help="Layer for --export (default: elevation)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.png_scale < 1:
        raise SystemExit("--png-scale must be >= 1")

    view_size: int = clamp_view_size(
        args.view_size if args.view_size > 0 else default_view_size(args.size)
    )

    if args.export_all is not None:
        print(f"Generating world (seed={args.seed}, size={args.size})...")
        world = generate_world(args.size, args.seed)
        out_dir: Path = args.export_all
        out_dir.mkdir(parents=True, exist_ok=True)
        for layer in LAYER_ORDER:
            path = out_dir / f"seed{args.seed}_{layer.value}.png"
            export_layer(world, layer, path, args.png_scale, grid=False)
        return

    if args.export is not None:
        print(f"Generating world (seed={args.seed}, size={args.size})...")
        world = generate_world(args.size, args.seed)
        export_layer(
            world,
            Layer(args.layer),
            args.export,
            args.png_scale,
            grid=False,
        )
        return

    WorldgenViewerApp(
        grid_size=args.size,
        seed=args.seed,
        view_size=view_size,
        png_output_dir=args.png_dir,
        png_scale=args.png_scale,
    ).run()


if __name__ == "__main__":
    main()
