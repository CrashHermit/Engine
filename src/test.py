from textual.app import App, ComposeResult
from textual_canvas import Canvas  # Dave Pearson's package
from textual.color import Color

# The 8-bit grid layout coordinates for a classic Space Invader sprite
INVADER_PIXELS = [
    (2, 0), (8, 0),
    (3, 1), (7, 1),
    (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (8, 2),
    (1, 3), (2, 3), (4, 3), (5, 3), (6, 3), (8, 3), (9, 3),
    (0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4), (10, 4),
    (0, 5), (2, 5), (3, 5), (4, 5), (5, 5), (6, 5), (7, 5), (8, 5), (10, 5),
    (0, 6), (2, 6), (8, 6), (10, 6),
    (3, 7), (4, 7), (6, 7), (7, 7)
]

class PixelArtApp(App):
    CSS = """
    Screen {
        align: center middle;
        background: #1a1a1a;
    }
    Canvas {
        border: solid magenta;
        background: black;
    }
    """

    def compose(self) -> ComposeResult:
        # Give the canvas container specific cell dimensions
        yield Canvas(30, 15)

    def on_mount(self) -> None:
        canvas = self.query_one(Canvas)
        
        # Shift drawing positions into the center of the canvas
        offset_x = 9
        offset_y = 3
        
        # Loop through coordinates to color the invader sprite
        for x, y in INVADER_PIXELS:
            canvas.set_pixel(offset_x + x, offset_y + y, Color.parse("green"))

if __name__ == "__main__":
    PixelArtApp().run()
