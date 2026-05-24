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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        from .world_list import WorldListScreen
        from ..modals.create_world import CreateWorldModal

        if event.button.id == "btn-load":
            self.app.push_screen(WorldListScreen())
        elif event.button.id == "btn-new":
            def _on_dismiss(result: dict | None) -> None:
                if result:
                    self.app.push_screen(WorldListScreen())
            self.app.push_screen(CreateWorldModal(), callback=_on_dismiss)
