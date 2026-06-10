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
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Static
from textual_canvas import Canvas

from scripts.worldgen_render import (
    LAYER_DESCRIPTIONS,
    LAYER_LABELS,
    LAYER_ORDER,
    Layer,
    generate_world,
    rasterize,
)
from src.worldgen.model import WorldData

# Re-export for backwards compatibility if anything imported from view_worldgen
__all__ = ["Layer", "generate_world", "rasterize"]


def draw_layer(canvas: Canvas, world_data: WorldData, layer: Layer) -> None:
    pixels = rasterize(world_data, layer)
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
        width: 28;
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

    #layer-bar {
        height: auto;
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
        Binding("1", "layer('elevation')", "Elevation"),
        Binding("2", "layer('temperature')", "Temperature"),
        Binding("3", "layer('precipitation')", "Precipitation"),
        Binding("4", "layer('savagery')", "Savagery"),
        Binding("5", "layer('alignment')", "Alignment"),
        Binding("6", "layer('biomes')", "Biomes"),
        Binding("7", "layer('hydrology')", "Hydrology"),
        Binding("8", "layer('rivers')", "Rivers"),
        Binding("9", "layer('landmasses')", "Landmasses"),
        Binding("0", "layer('mesh')", "Mesh"),
    ]

    def __init__(self, grid_size: int, seed: int) -> None:
        super().__init__()
        self._grid_size = grid_size
        self._seed = seed
        self._layer = Layer.ELEVATION
        self._world_data = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("Layer", id="info-title")
                yield Static("", id="info-desc")
                yield Static("", id="info-meta")
                with Vertical(id="layer-bar"):
                    for index, layer in enumerate(LAYER_ORDER, start=1):
                        yield Button(
                            f"{index}  {LAYER_LABELS[layer]}",
                            id=f"btn-{layer.value}",
                            variant="default",
                        )
            with Vertical(id="map-area"):
                yield Canvas(self._grid_size, self._grid_size, Color(0, 0, 0))
        yield Footer()

    def on_mount(self) -> None:
        self._regenerate()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id and button_id.startswith("btn-"):
            self.action_layer(button_id.removeprefix("btn-"))

    def _update_ui(self) -> None:
        grid_label = f"{self._grid_size}x{self._grid_size}"
        self.sub_title = f"seed {self._seed}  |  grid {grid_label}"
        self.query_one("#info-title", Static).update(LAYER_LABELS[self._layer])
        self.query_one("#info-desc", Static).update(LAYER_DESCRIPTIONS[self._layer])
        self.query_one("#info-meta", Static).update(
            "Press 1-9, 0 or click a layer.\n[r] re-roll  [q] quit"
        )
        for layer in LAYER_ORDER:
            button = self.query_one(f"#btn-{layer.value}", Button)
            button.set_class(self._layer == layer, "-active")

    def _regenerate(self) -> None:
        self._world_data = generate_world(self._grid_size, self._seed)
        draw_layer(self.query_one(Canvas), self._world_data, self._layer)
        self._update_ui()

    def action_reroll(self) -> None:
        self._seed = random.randint(0, 2**31 - 1)
        self._regenerate()

    def action_layer(self, layer_name: str) -> None:
        self._layer = Layer(layer_name)
        if self._world_data is not None:
            draw_layer(self.query_one(Canvas), self._world_data, self._layer)
            self._update_ui()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="View worldgen pipeline output.")
    parser.add_argument("--seed", type=int, default=0, help="World seed (default: 0)")
    parser.add_argument("--size", type=int, default=80, help="Grid size (default: 80)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    WorldgenViewerApp(grid_size=args.size, seed=args.seed).run()


if __name__ == "__main__":
    main()
