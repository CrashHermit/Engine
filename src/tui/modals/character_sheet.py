from arcadedb_embedded.graph import Vertex
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual.containers import Horizontal, Vertical

from src.core.model.database import EdgeType
from src.database.repository.character import CharacterRepository
from src.tui.widgets.pip_selector import PipSelector


class CharacterSheetModal(ModalScreen[None]):
    """Read-only character sheet for the active character."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("c", "dismiss", "Close"),
    ]

    def __init__(self, character: Vertex, repo: CharacterRepository) -> None:
        super().__init__()
        self._character = character
        self._repo = repo

    def compose(self) -> ComposeResult:
        with Vertical(id="character-sheet"):
            yield Label("CHARACTER SHEET", id="sheet-title")

            with Horizontal(id="sheet-identity"):
                with Vertical(id="sheet-left"):
                    yield Label("", id="sheet-name")
                    yield Static("", id="sheet-description")
                with Vertical(id="sheet-right"):
                    yield Label("Attributes", id="attrs-title")
                    yield PipSelector("Corpus", max_val=4, value=0, readonly=True, id="pip-corpus")
                    yield PipSelector("Mens", max_val=4, value=0, readonly=True, id="pip-mens")
                    yield PipSelector("Anima", max_val=4, value=0, readonly=True, id="pip-anima")

            yield Label("Condition", id="condition-title")
            yield Static("HP: — / —  |  Wounds: —  |  Status: —", id="sheet-condition")

            yield Label("Equipment", id="equipment-title")
            yield Static("—", id="sheet-equipment")

            yield Label("Inventory", id="inventory-title")
            yield Static("—", id="sheet-inventory")

            yield Label("Personality", id="personality-title")
            with Horizontal(id="personality-traits"):
                yield PipSelector("Extraversion", min_val=1, max_val=5, value=1, readonly=True, id="pip-extra")
                yield PipSelector("Openness", min_val=1, max_val=5, value=1, readonly=True, id="pip-open")
                yield PipSelector("Agreeableness", min_val=1, max_val=5, value=1, readonly=True, id="pip-agree")
                yield PipSelector("Neuroticism", min_val=1, max_val=5, value=1, readonly=True, id="pip-neuro")
                yield PipSelector("Conscientiousness", min_val=1, max_val=5, value=1, readonly=True, id="pip-consc")

            yield Button("Close", id="btn-close", variant="default")

    def on_mount(self) -> None:
        self.query_one("#sheet-name", Label).update(self._character.get(name="name") or "—")
        self.query_one("#sheet-description", Static).update(self._character.get(name="description") or "")

        try:
            corpus = self._repo.get_attribute_value(self._repo.get_corpus(self._character))
            mens = self._repo.get_attribute_value(self._repo.get_mens(self._character))
            anima = self._repo.get_attribute_value(self._repo.get_anima(self._character))
            self.query_one("#pip-corpus", PipSelector).value = corpus
            self.query_one("#pip-mens", PipSelector).value = mens
            self.query_one("#pip-anima", PipSelector).value = anima
        except Exception:
            pass

        try:
            personality = self._repo.get_personality(self._character)
            self.query_one("#pip-extra", PipSelector).value = self._repo.get_trait_value(personality, EdgeType.HAS_EXTRAVERSION)
            self.query_one("#pip-open", PipSelector).value = self._repo.get_trait_value(personality, EdgeType.HAS_OPENNESS)
            self.query_one("#pip-agree", PipSelector).value = self._repo.get_trait_value(personality, EdgeType.HAS_AGREEABLENESS)
            self.query_one("#pip-neuro", PipSelector).value = self._repo.get_trait_value(personality, EdgeType.HAS_NEUROTICISM)
            self.query_one("#pip-consc", PipSelector).value = self._repo.get_trait_value(personality, EdgeType.HAS_CONSCIENTIOUSNESS)
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close":
            self.dismiss()
