from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Collapsible, RichLog, Static
from textual.containers import Horizontal, Vertical
from textual.worker import get_current_worker

from ..widgets.chat_panel import ChatPanel

_PLACEHOLDER_SCENE = """\
[bold #c9a84c]The Ruined Chapel[/bold #c9a84c]

The rain hammers the cracked flagstones. Torchlight flickers across \
moss-covered walls where ancient inscriptions have been worn smooth \
by centuries of damp.

A heavy door hangs ajar to the north. Something shifts in the \
shadows beyond the altar — too deliberate to be the wind.\
"""


class GameScreen(Screen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("c", "character_sheet", "Character Sheet"),
    ]

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
        self.query_one("#scene-log", RichLog).write(_PLACEHOLDER_SCENE)

    def on_collapsible_toggled(self, event: Collapsible.Toggled) -> None:
        col = self.query_one("#scene-collapsible")
        col.styles.width = "auto" if event.collapsible.collapsed else "40%"

    def on_chat_panel_message_sent(self, event: ChatPanel.MessageSent) -> None:
        self.process_chat_message(event.text, event.channel)

    @work(exclusive=True, thread=True)
    def process_chat_message(self, text: str, channel: str) -> None:
        if get_current_worker().is_cancelled:
            return

    def action_character_sheet(self) -> None:
        from ..modals.character_sheet import CharacterSheetModal
        self.app.push_screen(CharacterSheetModal())
