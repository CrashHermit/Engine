from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView

from src.tui.modals.confirm_modal import ConfirmDeleteWorldModal
from src.tui.modals.create_world import CreateWorldModal
from src.tui.screens.world_detail import WorldDetailScreen


class WorldListScreen(Screen):
    BINDINGS: list[BindingType] = [
        Binding(key="escape", action="app.pop_screen", description="Back")
    ]

    def __init__(self) -> None:
        super().__init__()
        self._worlds: list[str] = []

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
        self._reload_worlds()

    def _reload_worlds(self) -> None:
        self._worlds = self.app.connection.list_databases()
        self._refresh_world_list()

    def _selected_world_name(self) -> str | None:
        item: ListItem | None = self.query_one("#world-list", ListView).highlighted_child
        if item is None:
            return None
        return str(item.query_one(Label).content)

    def _refresh_world_list(self) -> None:
        list_view: ListView = self.query_one("#world-list", ListView)
        list_view.clear()
        for name in self._worlds:
            list_view.append(item=ListItem(Label(content=name)))

    def _on_create_world_dismissed(self, result: dict[str, str] | None) -> None:
        if result:
            self._reload_worlds()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-new":
            self.app.push_screen(CreateWorldModal(), callback=self._on_create_world_dismissed)
        elif event.button.id == "btn-enter":
            world_name: str | None = self._selected_world_name()
            if world_name:
                if self.app.factory is None:
                    self.app.notify(
                        message="Session still starting up, try again.", severity="warning"
                    )
                    return
                try:
                    services = self.app.factory.open(world_name)
                except Exception as e:
                    self.app.notify(message=f"Failed to open world: {e}", severity="error")
                    return
                self.app.push_screen(WorldDetailScreen(world_name=world_name, services=services))
        elif event.button.id == "btn-delete":
            world_name: str | None = self._selected_world_name()
            if world_name is None:
                return
            self.app.push_screen(
                ConfirmDeleteWorldModal(world_name=world_name),
                callback=lambda confirmed: self._on_delete_world_confirmed(
                    world_name=world_name, confirmed=confirmed
                ),
            )

    def _on_delete_world_confirmed(self, world_name: str, confirmed: bool | None) -> None:
        if not confirmed:
            return
        try:
            self.app.connection.delete_database(name=world_name)
        except Exception as e:
            self.app.notify(message=f"Failed to delete world: {e}", severity="error")
            return
        self._reload_worlds()
        self.app.notify(message=f'Deleted world "{world_name}"')
