from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import RichLog, Static
from textual.containers import Horizontal, Vertical

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
                yield RichLog(id="scene-panel", highlight=True, markup=True)
                yield ChatPanel(id="chat-panel")
            yield Static(
                "HP: — / —  |  Status: Normal  |  Location: —",
                id="status-bar",
            )

    def on_mount(self) -> None:
        self.query_one("#scene-panel", RichLog).write(_PLACEHOLDER_SCENE)

    def action_character_sheet(self) -> None:
        from ..modals.character_sheet import CharacterSheetModal
        self.app.push_screen(CharacterSheetModal())
