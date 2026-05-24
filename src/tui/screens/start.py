from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Label
from textual.containers import Vertical


class StartScreen(Screen):
    BINDINGS = [Binding("escape", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        with Vertical(id="start-container"):
            yield Label("DARK ADVENTURES", id="start-title")
            yield Button("Load World", id="btn-load", variant="primary")
            yield Button("New World", id="btn-new", variant="default")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        from .world_list import WorldListScreen
        from ..modals.create_world import CreateWorldModal

        if event.button.id == "btn-load":
            self.app.push_screen(WorldListScreen())
        elif event.button.id == "btn-new":
            result = await self.app.push_screen_wait(CreateWorldModal())
            if result:
                self.app.push_screen(WorldListScreen())
