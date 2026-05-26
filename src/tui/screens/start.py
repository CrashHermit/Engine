from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import Screen
from textual.widgets import Button, Label
from textual.containers import Vertical
from src.tui.screens.world_list import WorldListScreen
from src.tui.modals.create_world import CreateWorldModal

class StartScreen(Screen):
    BINDINGS: list[BindingType] = [Binding(key="escape", action="app.quit", description="Quit")]

    def compose(self) -> ComposeResult:
        with Vertical(id="start-container"):
            yield Label(content="DARK ADVENTURES", id="start-title")
            yield Button(label="Load World", id="btn-load", variant="primary")
            yield Button(label="New World", id="btn-new", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-load":
            self.app.push_screen(WorldListScreen())
        elif event.button.id == "btn-new":
            def _on_dismiss(result: dict[str, str] | None) -> None:
                if result:
                    self.app.push_screen(WorldListScreen(created_world=result))
            self.app.push_screen(CreateWorldModal(), callback=_on_dismiss)
