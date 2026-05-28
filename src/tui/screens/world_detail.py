import arcadedb_embedded as arcadedb
from arcadedb_embedded.graph import Vertex
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView, Static
from textual.containers import Horizontal, Vertical

from src.tui.screens.game import GameScreen
from src.tui.modals.create_character import CreateCharacterModal
from src.tui.modals.confirm_modal import ConfirmModal
from src.tui.widgets.pip_selector import PipSelector
from src.database.repository.base import BaseRepository
from src.database.repository.character import CharacterRepository
from src.database.schema import SchemaManager


class WorldDetailScreen(Screen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(self, *, world_name: str) -> None:
        super().__init__()
        self.world_name: str = world_name
        self._db: arcadedb.Database | None = None
        self._character_repo: CharacterRepository | None = None
        self._characters: list[Vertex] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="detail-panels"):
            with Vertical(id="char-list-panel"):
                yield Label("Characters", id="char-list-title")
                yield ListView(id="char-list")
            with Vertical(id="char-detail-panel"):
                yield Label("—", id="char-name")
                yield Static("", id="char-description")
                yield PipSelector("Corpus", max_val=4, value=0, readonly=True, id="pip-corpus")
                yield PipSelector("Mens", max_val=4, value=0, readonly=True, id="pip-mens")
                yield PipSelector("Anima", max_val=4, value=0, readonly=True, id="pip-anima")
        with Horizontal(id="detail-actions"):
            yield Button("Back", id="btn-back", variant="default")
            yield Button("New Character", id="btn-new-char", variant="default")
            yield Button("Delete", id="btn-delete", variant="error")
            yield Button("Play", id="btn-play", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        try:
            self._db = self.app.connection.open_database(self.world_name)
            SchemaManager(self._db).ensure()
            base = BaseRepository(self._db)
            self._character_repo = CharacterRepository(base)
            self._characters = self._character_repo.list_characters()
        except Exception as e:
            self.app.notify(f"Failed to open world: {e}", severity="error")
            self.app.pop_screen()
            return
        self._refresh_character_list()

    def _selected_character(self) -> Vertex | None:
        lv = self.query_one("#char-list", ListView)
        idx = lv.index
        if idx is None or not (0 <= idx < len(self._characters)):
            return None
        return self._characters[idx]

    def _clear_character_detail(self) -> None:
        self.query_one("#char-name", Label).update("—")
        self.query_one("#char-description", Static).update("No characters yet. Create one to begin.")
        self.query_one("#pip-corpus", PipSelector).value = 0
        self.query_one("#pip-mens", PipSelector).value = 0
        self.query_one("#pip-anima", PipSelector).value = 0

    def _refresh_character_list(self) -> None:
        list_view = self.query_one("#char-list", ListView)
        list_view.clear()
        for character in self._characters:
            name = character.get(name="name") or "Unnamed"
            list_view.append(ListItem(Label(name)))
        if not self._characters:
            self._clear_character_detail()

    def _display_character(self, character: Vertex) -> None:
        self.query_one("#char-name", Label).update(character.get(name="name") or "—")
        self.query_one("#char-description", Static).update(character.get(name="description") or "")
        try:
            repo = self._character_repo
            corpus = repo.get_attribute_value(repo.get_corpus(character))
            mens = repo.get_attribute_value(repo.get_mens(character))
            anima = repo.get_attribute_value(repo.get_anima(character))
        except Exception:
            corpus = mens = anima = 0
        self.query_one("#pip-corpus", PipSelector).value = corpus
        self.query_one("#pip-mens", PipSelector).value = mens
        self.query_one("#pip-anima", PipSelector).value = anima

    def _on_create_character_dismissed(self, result: dict[str, int | str] | None) -> None:
        if result is None or self._character_repo is None:
            return
        try:
            self._character_repo.create_full_character(
                name=str(result["name"]),
                description=str(result.get("description", "")),
                corpus=int(result.get("corpus", 0)),
                mens=int(result.get("mens", 0)),
                anima=int(result.get("anima", 0)),
                extraversion=int(result.get("extraversion", 1)),
                openness=int(result.get("openness", 1)),
                agreeableness=int(result.get("agreeableness", 1)),
                neuroticism=int(result.get("neuroticism", 1)),
                conscientiousness=int(result.get("conscientiousness", 1)),
            )
            self._characters = self._character_repo.list_characters()
            self._refresh_character_list()
        except Exception as e:
            self.app.notify(f"Failed to create character: {e}", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-new-char":
            self.app.push_screen(
                CreateCharacterModal(), callback=self._on_create_character_dismissed
            )
        elif event.button.id == "btn-play":
            character = self._selected_character()
            if character is not None and self._db is not None:
                self.app.push_screen(GameScreen(character=character, database=self._db))
        elif event.button.id == "btn-delete":
            character = self._selected_character()
            if character is None:
                return
            name = character.get(name="name") or "this character"
            self.app.push_screen(
                ConfirmModal(
                    title="Delete Character?",
                    message=f'Are you sure you want to delete "{name}"?',
                ),
                callback=lambda confirmed: self._on_delete_character_confirmed(character, confirmed),
            )

    def _on_delete_character_confirmed(self, character: Vertex, confirmed: bool | None) -> None:
        if not confirmed or self._character_repo is None:
            return
        try:
            name = character.get(name="name") or "character"
            self._character_repo.delete_character(character)
            self._characters = self._character_repo.list_characters()
            self._refresh_character_list()
            self.app.notify(f'Deleted "{name}"')
        except Exception as e:
            self.app.notify(f"Failed to delete character: {e}", severity="error")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is None:
            self._clear_character_detail()
            return
        lv = self.query_one("#char-list", ListView)
        idx = lv.index
        if idx is not None and 0 <= idx < len(self._characters):
            self._display_character(self._characters[idx])
