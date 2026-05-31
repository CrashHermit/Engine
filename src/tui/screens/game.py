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
from src.state import GraphState
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

        graph_service = self._services.graph_service
        config = graph_service.thread_config(
            world_name=self._services.world_name,
            character_id=self._character.id,
            run_id=self._run_id,
        )

        try:
            # A pending interrupt on this thread means we are mid-clarification,
            # so this message is the player's answer; otherwise it's a new action.
            resuming = await graph_service.is_paused(config=config)

            if resuming:
                result = await graph_service.resume(text, config=config)
            else:
                result = await graph_service.ainvoke(self._build_graph_state(text), config=config)

            if get_current_worker().is_cancelled:
                return

            question = graph_service.interrupt_question(result)
            if question is not None:
                log.write(f"[bold #7ec8e3]Intent Alignment:[/bold #7ec8e3] {escape(question)}")
                return

            ai_msg = result.get("ai_message")
            if ai_msg is not None:
                self._message_history = result.get("message_history", self._message_history)
                content = (
                    ai_msg.content if hasattr(ai_msg, "content") else ai_msg.get("content", "")
                )
                log.write(f"[bold #c9a84c]Narrator:[/bold #c9a84c] {escape(content)}")
            else:
                log.write("[dim red]No response from graph.[/dim red]")

            # Action finished; next message starts a brand-new thread.
            self._run_id = graph_service.new_run_id()
        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {escape(str(e))}")
        finally:
            chat_panel.set_processing(False)

    def _build_graph_state(self, text: str) -> GraphState:
        state = self._location_state
        entities_at_location = (
            [f"{e.name}: {e.description}. Location: {e.scene_position}" for e in state.entities]
            if state is not None
            else []
        )
        return GraphState(
            message_history=self._message_history,
            intent_alignment_history=[],
            human_message=Message(role="human", content=text, name=""),
            ai_message=None,
            question=None,
            is_intent_alignment_achieved=None,
            character_name=self._character.name or "",
            character_description=self._character.description or "",
            location_name=state.location.name if state else "",
            location_description=state.location.description if state else "",
            entities_at_location=entities_at_location,
        )
