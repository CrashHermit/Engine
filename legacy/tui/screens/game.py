from rich.markup import escape
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Input, RichLog

from src.core.model.character import CharacterData
from src.core.model.location import LocationState
from src.service.container import ServiceContainer
from src.session.coordinator import GameCoordinator
from src.session.result import (
    CharacterLost,
    ClarifyingQuestion,
    Narration,
    ResistanceOffer,
    TargetDefeated,
    TargetReturned,
    TargetSuspended,
    TraumaGained,
    TurnError,
    TurnEvent,
)
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
        self._coordinator = GameCoordinator(character=character, services=services)

    def compose(self) -> ComposeResult:
        with Vertical(id="game-layout"):
            with Horizontal(id="game-panels"):
                yield LeftPanel(id="left-panel")
                yield ChatPanel(
                    character_name=self._coordinator.character.name or "You",
                    id="chat-panel",
                )

    def on_mount(self) -> None:
        state = self._coordinator.enter()
        if state is None:
            self.app.notify("This world has no starting location.", severity="error")
            self.app.pop_screen()
            return
        self._show_location(state)

    def on_key(self, event: Key) -> None:
        chat_input = self.query_one("#msg-input", Input)
        if chat_input.has_focus:
            return
        location = self._coordinator.current_location
        if event.key.isdigit() and location is not None:
            index = int(event.key) - 1
            neighbors = location.neighbors
            if 0 <= index < len(neighbors):
                event.stop()
                state = self._coordinator.move(neighbors[index].id)
                if state is not None:
                    self._show_location(state)

    def _show_location(self, state: LocationState) -> None:
        location = state.location
        exits = (
            " · ".join(f"[{i + 1}] {n.name}" for i, n in enumerate(state.neighbors))
            or "No exits."
        )
        display_entities = [f"{e.name} — {e.scene_position}" for e in state.entities]

        panel = self.query_one(LeftPanel)
        panel.write_scene(location.name, location.description, exits, display_entities)
        panel.update_info(
            character_name=self._coordinator.character.name or "—",
            location_name=location.name,
        )

    def on_chat_panel_message_sent(self, event: ChatPanel.MessageSent) -> None:
        self.process_chat_message(event.text)

    def action_character_sheet(self) -> None:
        self.app.push_screen(CharacterSheetModal(self._coordinator.character))

    @work(exclusive=True)
    async def process_chat_message(self, text: str) -> None:
        chat_panel = self.query_one(ChatPanel)
        log = self.query_one("#chat-log", RichLog)
        chat_panel.set_processing(True)
        try:
            async for event in self._coordinator.submit(text):
                self._render_event(event, log)
        finally:
            chat_panel.set_processing(False)

    def _render_event(self, event: TurnEvent, log: RichLog) -> None:
        match event:
            case ClarifyingQuestion(question):
                log.write(
                    f"[bold #7ec8e3]Intent Alignment:[/bold #7ec8e3] {escape(question)}"
                )
            case Narration(text):
                if text:
                    log.write(f"[bold #c9a84c]Narrator:[/bold #c9a84c] {escape(text)}")
                else:
                    log.write("[dim red]No response from graph.[/dim red]")
            case ResistanceOffer(offer):
                log.write(f"[bold #a87ee3]Resistance:[/bold #a87ee3] {escape(offer)}")
            case TraumaGained(trauma):
                trauma_max = self._coordinator.character.trauma_max
                log.write(
                    f"[bold #d98c5f]Trauma:[/bold #d98c5f] stress broke you — "
                    f"trauma is now {trauma} / {trauma_max}."
                )
            case CharacterLost():
                log.write(
                    "[bold red]Lost:[/bold red] the trauma has claimed you. "
                    "This character is gone."
                )
            case TargetDefeated(name):
                log.write(
                    f"[bold #6ec06e]Defeated:[/bold #6ec06e] {escape(name)} is down."
                )
            case TargetSuspended(name):
                log.write(
                    f"[bold #6ec06e]Neutralized:[/bold #6ec06e] {escape(name)}"
                    " is out of the fight."
                )
            case TargetReturned(name):
                log.write(
                    f"[bold #d98c5f]Returned:[/bold #d98c5f] {escape(name)}"
                    " is back in the fight."
                )
            case TurnError(message):
                log.write(f"[bold red]Error:[/bold red] {escape(message)}")
