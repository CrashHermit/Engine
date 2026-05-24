from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView, Static
from textual.containers import Horizontal, Vertical

from ..widgets.pip_selector import PipSelector


class WorldDetailScreen(Screen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    # TODO: replace with CharacterRepository.get_user_characters()
    _PLACEHOLDER_CHARACTERS = ["Aldric the Bold", "Sister Mara", "Thane Vexx"]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="detail-panels"):
            with Vertical(id="char-list-panel"):
                yield Label("Characters", id="char-list-title")
                yield ListView(
                    *[ListItem(Label(name)) for name in self._PLACEHOLDER_CHARACTERS],
                    id="char-list",
                )
            with Vertical(id="char-detail-panel"):
                yield Label("Aldric the Bold", id="char-name")
                yield Static(
                    "A seasoned warrior from the northern provinces.",
                    id="char-description",
                )
                yield PipSelector("Corpus", max_val=4, value=2, readonly=True, id="pip-corpus")
                yield PipSelector("Mens", max_val=4, value=1, readonly=True, id="pip-mens")
                yield PipSelector("Anima", max_val=4, value=2, readonly=True, id="pip-anima")
        with Horizontal(id="detail-actions"):
            yield Button("Back", id="btn-back", variant="default")
            yield Button("New Character", id="btn-new-char", variant="default")
            yield Button("Delete", id="btn-delete", variant="error")
            yield Button("Play", id="btn-play", variant="success")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        from .game import GameScreen
        from ..modals.create_character import CreateCharacterModal

        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-new-char":
            self.app.push_screen(CreateCharacterModal())
        elif event.button.id == "btn-play":
            self.app.push_screen(GameScreen())
        elif event.button.id == "btn-delete":
            pass  # TODO: confirmation dialog then CharacterRepository.delete()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        # TODO: load real character data from CharacterRepository
        pass
