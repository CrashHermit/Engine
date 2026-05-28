import arcadedb_embedded as arcadedb
from arcadedb_embedded.graph import Vertex
from rich.markup import escape
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Input
from textual.containers import Horizontal, Vertical
from textual.worker import get_current_worker

from src.core.model.message import Message
from src.database.repository.base import BaseRepository
from src.database.repository.character import CharacterRepository
from src.database.repository.location import LocationRepository
from src.graph import Graph
from src.state import GraphState
from src.tui.widgets.chat_panel import ChatPanel
from src.tui.widgets.left_panel import LeftPanel
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
        self._message_history: list[Message] = []
        self._graph = None

    def compose(self) -> ComposeResult:
        with Vertical(id="game-layout"):
            with Horizontal(id="game-panels"):
                yield LeftPanel(id="left-panel")
                yield ChatPanel(id="chat-panel")

    def on_mount(self) -> None:
        base = BaseRepository(self._db)
        self._location_repo = LocationRepository(base)
        self._character_repo = CharacterRepository(base)
        self._graph = Graph().build().compile()

        location = self._character_repo.get_current_location(self._character)
        if location is None:
            self.query_one("#scene-log", RichLog).write("[red]No starting location.[/red]")
            return
        self._show_location(location)

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
        name = location.get(name="name") or "Unknown"
        description = location.get(name="description") or ""
        exits = " · ".join(
            f"[{i + 1}] {n.get(name='name')}"
            for i, n in enumerate(self._neighbors)
        ) or "No exits."

        panel = self.query_one(LeftPanel)
        panel.write_scene(name, description, exits)
        panel.update_info(
            character_name=self._character.get(name="name") or "—",
            location_name=name,
        )

    def on_chat_panel_message_sent(self, event: ChatPanel.MessageSent) -> None:
        self.process_chat_message(event.text, event.channel)

    def action_character_sheet(self) -> None:
        self.app.push_screen(CharacterSheetModal(self._character, self._character_repo))

    @work(exclusive=True)
    async def process_chat_message(self, text: str, channel: str) -> None:
        if get_current_worker().is_cancelled or self._graph is None:
            return
        if channel != "ic":
            return

        human_msg = Message(role="human", content=text, name="")
        state = GraphState(
            message_history=self._message_history,
            human_message=human_msg,
            ai_message=None,
        )

        result = await self._graph.ainvoke(state)

        if get_current_worker().is_cancelled:
            return

        self._message_history = result.get("message_history", self._message_history)
        ai_msg = result.get("ai_message")
        if ai_msg is None:
            return

        content = ai_msg.content if hasattr(ai_msg, "content") else ai_msg.get("content", "")
        log = self.query_one("#chat-log", RichLog)
        log.write(f"[bold #c9a84c]Narrator:[/bold #c9a84c] {escape(content)}")
