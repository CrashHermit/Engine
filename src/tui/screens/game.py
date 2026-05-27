import arcadedb_embedded as arcadedb
from arcadedb_embedded.graph import Vertex
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Collapsible, Input, RichLog, Static
from textual.containers import Horizontal, Vertical
from textual.worker import get_current_worker

from src.database.repository.base import BaseRepository
from src.database.repository.character import CharacterRepository
from src.database.repository.location import LocationRepository
from src.tui.widgets.chat_panel import ChatPanel
from src.tui.modals.character_sheet import CharacterSheetModal

class GameScreen(Screen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("c", "character_sheet", "Character Sheet"),
    ]

    def __init__(self, *, character: Vertex, database: arcadedb.Database) -> None:
        super().__init__()
        self._character = character
        self._db = database
        self._neighbors: list[Vertex] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="game-layout"):
            with Horizontal(id="game-panels"):
                with Collapsible(title="Scene", id="scene-collapsible"):
                    yield RichLog(id="scene-log", highlight=True, markup=True, wrap=True)
                yield ChatPanel(id="chat-panel")
            yield Static(
                "HP: — / —  |  Status: Normal  |  Location: —",
                id="status-bar",
            )

    def on_mount(self) -> None:
        base = BaseRepository(self._db)
        self._location_repo = LocationRepository(base)
        self._character_repo = CharacterRepository(base)

        location = self._character_repo.get_current_location(self._character)
        if location is None:
            self.query_one("#scene-log", RichLog).write("[red]No starting location.[/red]")
            return
        self._show_location(location)

    def on_collapsible_toggled(self, event: Collapsible.Toggled) -> None:
        col = self.query_one("#scene-collapsible")
        col.styles.width = "auto" if event.collapsible.collapsed else "40%"

    def on_key(self, event: Key) -> None:
        chat_input = self.query_one("#msg-input", Input)
        if chat_input.has_focus:
            return
        if event.key.isdigit():
            index = int(event.key) - 1
            if 0 <= index < len(self._neighbors):
                event.stop()
                self._move(self._neighbors[index])

    def _move(self, destination: Vertex) -> None:
        self._character_repo.move_character(self._character, destination)
        self._show_location(destination)

    def _show_location(self, location: Vertex) -> None:
        self._neighbors = self._location_repo.get_neighbors(location)
        name = location.get(name="name")
        description = location.get(name="description")
        exits = " · ".join(
            f"[{i + 1}] {n.get(name='name')}"
            for i, n in enumerate(self._neighbors)
        ) or "No exits."

        log = self.query_one("#scene-log", RichLog)
        log.write(
            f"\n[bold #c9a84c]{name}[/bold #c9a84c]\n\n"
            f"{description}\n\n"
            f"[dim]{exits}[/dim]"
        )

    def on_chat_panel_message_sent(self, event: ChatPanel.MessageSent) -> None:
        self.process_chat_message(event.text, event.channel)

    def action_character_sheet(self) -> None:
        self.app.push_screen(CharacterSheetModal())

    @work(exclusive=True, thread=True)
    def process_chat_message(self, text: str, channel: str) -> None:
        if get_current_worker().is_cancelled:
        	return


