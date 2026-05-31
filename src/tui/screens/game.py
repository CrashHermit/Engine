from rich.markup import escape
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Input, RichLog
from textual.worker import get_current_worker

from src.core.model.character import CharacterData
from src.core.model.location import LocationState
from src.core.model.message import Message
from src.service.container import ServiceContainer
from src.service.turn import CompletedResult, PausedResult, TurnContext
from src.tui.modals.character_sheet import CharacterSheetModal
from src.tui.widgets.chat_panel import ChatPanel
from src.tui.widgets.left_panel import LeftPanel


class GameScreen(Screen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("c", "character_sheet", "Character Sheet"),
    ]

    def __init__(self, *, character: CharacterData, services: ServiceContainer) -> None:
        super().__init__()
        self._character = character
        self._services = services
        self._location_state: LocationState | None = None
        self._message_history: list[Message] = []
        # One thread per in-progress action. Reused while clarifying intent,
        # rotated once an action completes so the next action starts fresh.
        self._run_id = self._services.graph_service.new_run_id()

    def compose(self) -> ComposeResult:
        with Vertical(id="game-layout"):
            with Horizontal(id="game-panels"):
                yield LeftPanel(id="left-panel")
                yield ChatPanel(character_name=self._character.name or "You", id="chat-panel")

    def on_mount(self) -> None:
        state = self._services.location.get_state_for_character(self._character.id)
        if state is None:
            self.app.notify("This world has no starting location.", severity="error")
            self.app.pop_screen()
            return
        self._show_location(state)

    def on_key(self, event: Key) -> None:
        chat_input = self.query_one("#msg-input", Input)
        if chat_input.has_focus:
            return
        if event.key.isdigit() and self._location_state is not None:
            index = int(event.key) - 1
            neighbors = self._location_state.neighbors
            if 0 <= index < len(neighbors):
                event.stop()
                self._move(neighbors[index].id)

    def _move(self, destination_id: str) -> None:
        state = self._services.location.move_character(self._character.id, destination_id)
        if state is not None:
            self._show_location(state)

    def _show_location(self, state: LocationState) -> None:
        self._location_state = state
        location = state.location
        exits = (
            " · ".join(f"[{i + 1}] {n.name}" for i, n in enumerate(state.neighbors)) or "No exits."
        )
        display_entities = [f"{e.name} — {e.scene_position}" for e in state.entities]

        panel = self.query_one(LeftPanel)
        panel.write_scene(location.name, location.description, exits, display_entities)
        panel.update_info(
            character_name=self._character.name or "—",
            location_name=location.name,
        )

    def on_chat_panel_message_sent(self, event: ChatPanel.MessageSent) -> None:
        self.process_chat_message(event.text)

    def action_character_sheet(self) -> None:
        self.app.push_screen(CharacterSheetModal(self._character))

    @work(exclusive=True)
    async def process_chat_message(self, text: str) -> None:
        if get_current_worker().is_cancelled:
            return

        chat_panel = self.query_one(ChatPanel)
        log = self.query_one("#chat-log", RichLog)
        chat_panel.set_processing(True)

        turn_service = self._services.turn
        ctx = TurnContext(
            character=self._character,
            location_state=self._location_state,
            message_history=self._message_history,
            run_id=self._run_id,
        )

        try:
            # A pending interrupt means we are mid-clarification; this message
            # is the player's answer. Otherwise it starts a new action.
            if await turn_service.is_paused(ctx):
                result = await turn_service.resume_turn(text, ctx)
            else:
                result = await turn_service.run_turn(text, ctx)

            if get_current_worker().is_cancelled:
                return

            if isinstance(result, PausedResult):
                log.write(f"[bold #7ec8e3]Intent Alignment:[/bold #7ec8e3] {escape(result.question)}")
                return

            assert isinstance(result, CompletedResult)
            if result.narration:
                self._message_history = result.message_history
                log.write(f"[bold #c9a84c]Narrator:[/bold #c9a84c] {escape(result.narration)}")
            else:
                log.write("[dim red]No response from graph.[/dim red]")

            # Action finished; next message starts a brand-new thread.
            self._run_id = result.next_run_id
        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {escape(str(e))}")
        finally:
            chat_panel.set_processing(False)
