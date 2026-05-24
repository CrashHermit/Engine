from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView
from textual.containers import Horizontal, Vertical


class WorldListScreen(Screen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    # TODO: replace with WorldStore.list_worlds()
    _PLACEHOLDER_WORLDS = ["The Forgotten Realm", "Ironhold", "Verdant Coast"]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="world-list-container"):
            yield Label("Your Worlds", id="worlds-title")
            yield ListView(
                *[ListItem(Label(name)) for name in self._PLACEHOLDER_WORLDS],
                id="world-list",
            )
            with Horizontal(id="world-list-footer"):
                yield Button("Back", id="btn-back", variant="default")
                yield Button("New World", id="btn-new", variant="primary")
                yield Button("Delete", id="btn-delete", variant="error")
                yield Button("Enter", id="btn-enter", variant="success")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        from .world_detail import WorldDetailScreen
        from ..modals.create_world import CreateWorldModal

        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-new":
            await self.app.push_screen_wait(CreateWorldModal())
        elif event.button.id == "btn-enter":
            self.app.push_screen(WorldDetailScreen())
        elif event.button.id == "btn-delete":
            pass  # TODO: confirmation dialog then WorldStore.delete(db_name)
