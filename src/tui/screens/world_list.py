from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView
from textual.containers import Horizontal, Vertical

from src.tui.screens.world_detail import WorldDetailScreen
from src.tui.modals.create_world import CreateWorldModal
from src.tui.modals.confirm_delete_world import ConfirmDeleteWorldModal


class WorldListScreen(Screen):
    BINDINGS: list[BindingType] = [Binding(key="escape", action="app.pop_screen", description="Back")]

    def __init__(self, *, created_world: dict[str, str] | None = None) -> None:
        super().__init__()
        self._worlds: list[str] = []
        self._created_world: dict[str, str] | None = created_world

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="world-list-container"):
            yield Label(content="Your Worlds", id="worlds-title")
            yield ListView(id="world-list")
            with Horizontal(id="world-list-footer"):
                yield Button(label="Back", id="btn-back", variant="default")
                yield Button(label="New World", id="btn-new", variant="primary")
                yield Button(label="Delete", id="btn-delete", variant="error")
                yield Button(label="Enter", id="btn-enter", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        self._worlds = self.app.connection.list_databases()
        if self._created_world and self._created_world["name"] not in self._worlds:
            self._worlds.append(self._created_world["name"])
        self._refresh_world_list()

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
            name: str = result["name"]
            if name not in self._worlds:
                self._worlds.append(name)
            self.app.world_characters.setdefault(name, [])
            self._refresh_world_list()

    def on_button_pressed(self, event: Button.Pressed) -> None:

        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-new":
            self.app.push_screen(CreateWorldModal(), callback=self._on_create_world_dismissed)
        elif event.button.id == "btn-enter":
            world_name: str | None = self._selected_world_name()
            if world_name:
                self.app.push_screen(WorldDetailScreen(world_name=world_name))
        elif event.button.id == "btn-delete":
            world_name: str | None = self._selected_world_name()
            if world_name is None:
                return
            self.app.push_screen(
                ConfirmDeleteWorldModal(world_name=world_name), 
                callback=lambda confirmed: self._on_delete_world_confirmed(world_name=world_name, confirmed=confirmed)
            )


    def _on_delete_world_confirmed(self, world_name: str, confirmed: bool | None) -> None:
        if not confirmed:
            return
        try:
            self.app.connection.delete_database(name=world_name)
        except Exception as e:
            self.app.notify(message=f"Failed to delete world: {e}", severity="error")
            return
        if world_name in self._worlds:
            self._worlds.remove(world_name)
        self.app.world_characters.pop(world_name, None)
        self.app.world_character_data.pop(world_name, None)
        self._refresh_world_list()
        self.app.notify(message=f'Deleted world "{world_name}"')
