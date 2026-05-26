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

    def __init__(self, *, world_name: str) -> None:
        super().__init__()
        self.world_name: str = world_name
        self._characters: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="detail-panels"):
            with Vertical(id="char-list-panel"):
                yield Label("Characters", id="char-list-title")
                yield ListView(id="char-list")
            with Vertical(id="char-detail-panel"):
                yield Label("—", id="char-name")
                yield Static("", id="char-description")
                yield PipSelector("Corpus", max_val=4, value=1, readonly=True, id="pip-corpus")
                yield PipSelector("Mens", max_val=4, value=1, readonly=True, id="pip-mens")
                yield PipSelector("Anima", max_val=4, value=1, readonly=True, id="pip-anima")
        with Horizontal(id="detail-actions"):
            yield Button("Back", id="btn-back", variant="default")
            yield Button("New Character", id="btn-new-char", variant="default")
            yield Button("Delete", id="btn-delete", variant="error")
            yield Button("Play", id="btn-play", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        self._characters = self.app.world_characters.setdefault(self.world_name, [])
        self._refresh_character_list()

    def _selected_character_name(self) -> str | None:
        item = self.query_one("#char-list", ListView).highlighted_child
        if item is None:
            return None
        return str(item.query_one(Label).content)

    def _clear_character_detail(self) -> None:
        self.query_one("#char-name", Label).update("—")
        self.query_one("#char-description", Static).update("No characters yet. Create one to begin.")

    def _refresh_character_list(self) -> None:
        list_view = self.query_one("#char-list", ListView)
        list_view.clear()
        for name in self._characters:
            list_view.append(ListItem(Label(name)))
        if not self._characters:
            self._clear_character_detail()

    def _on_create_character_dismissed(self, result: dict[str, int | str] | None) -> None:
        if result:
            name = str(result["name"])
            self._characters.append(name)
            self.app.world_character_data.setdefault(self.world_name, {})[name] = result
            self._refresh_character_list()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        from .game import GameScreen
        from ..modals.create_character import CreateCharacterModal

        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-new-char":
            self.app.push_screen(
                CreateCharacterModal(), callback=self._on_create_character_dismissed
            )
        elif event.button.id == "btn-play":
            self.app.push_screen(GameScreen())
        elif event.button.id == "btn-delete":
            name = self._selected_character_name()
            if name is None:
                return
            self._characters.remove(name)
            self._refresh_character_list()
            # TODO: confirmation dialog then CharacterRepository.delete()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is None:
            return
        name = str(event.item.query_one(Label).content)
        self.query_one("#char-name", Label).update(name)
        char = self.app.world_character_data.get(self.world_name, {}).get(name)
        if char:
            self.query_one("#char-description", Static).update(char.get("description", ""))
            self.query_one("#pip-corpus", PipSelector).value = char.get("corpus", 1)
            self.query_one("#pip-mens", PipSelector).value = char.get("mens", 1)
            self.query_one("#pip-anima", PipSelector).value = char.get("anima", 1)
        else:
            self.query_one("#char-description", Static).update("")
            self.query_one("#pip-corpus", PipSelector).value = 1
            self.query_one("#pip-mens", PipSelector).value = 1
            self.query_one("#pip-anima", PipSelector).value = 1
