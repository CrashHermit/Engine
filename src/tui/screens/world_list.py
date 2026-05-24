from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView
from textual.containers import Horizontal, Vertical

from .world_detail import WorldDetailScreen


class WorldListScreen(Screen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    # TODO: replace with WorldStore.list_worlds()
    _PLACEHOLDER_WORLDS = ["The Forgotten Realm", "Ironhold", "Verdant Coast"]

    def __init__(self, *, created_world: dict[str, str] | None = None) -> None:
        super().__init__()
        self._worlds = list(self._PLACEHOLDER_WORLDS)
        if created_world is not None:
            self._worlds.append(created_world["name"])

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="world-list-container"):
            yield Label("Your Worlds", id="worlds-title")
            yield ListView(id="world-list")
            with Horizontal(id="world-list-footer"):
                yield Button("Back", id="btn-back", variant="default")
                yield Button("New World", id="btn-new", variant="primary")
                yield Button("Delete", id="btn-delete", variant="error")
                yield Button("Enter", id="btn-enter", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        self._sync_world_characters()
        self._refresh_world_list()

    def _sync_world_characters(self) -> None:
        for name in self._worlds:
            if name in self.app.world_characters:
                continue
            if name in self._PLACEHOLDER_WORLDS:
                self.app.world_characters[name] = list(WorldDetailScreen._PLACEHOLDER_CHARACTERS)
            else:
                self.app.world_characters[name] = []

    def _selected_world_name(self) -> str | None:
        item = self.query_one("#world-list", ListView).highlighted_child
        if item is None:
            return None
        return str(item.query_one(Label).content)

    def _refresh_world_list(self) -> None:
        list_view = self.query_one("#world-list", ListView)
        list_view.clear()
        for name in self._worlds:
            list_view.append(ListItem(Label(name)))

    def _on_create_world_dismissed(self, result: dict[str, str] | None) -> None:
        if result:
            name = result["name"]
            self._worlds.append(name)
            self.app.world_characters[name] = []
            self._refresh_world_list()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        from ..modals.create_world import CreateWorldModal

        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-new":
            self.app.push_screen(CreateWorldModal(), callback=self._on_create_world_dismissed)
        elif event.button.id == "btn-enter":
            world_name = self._selected_world_name()
            if world_name:
                self.app.push_screen(WorldDetailScreen(world_name=world_name))
        elif event.button.id == "btn-delete":
            pass  # TODO: confirmation dialog then WorldStore.delete(db_name)
