from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static, TextArea
from textual.containers import Horizontal, Vertical

from ..widgets.pip_selector import PipSelector

_POOL_TOTAL = 5
_TRAIT_MAX = 5
_ATTR_IDS = ("pip-corpus", "pip-mens", "pip-anima")


class CreateCharacterModal(ModalScreen[dict[str, int | str] | None]):
    """Form for creating a new character with attribute pool and personality ratings."""

    BINDINGS = [Binding("escape", "dismiss_cancel", "Cancel")]

    def __init__(self) -> None:
        super().__init__()
        self._updating = False

    def compose(self) -> ComposeResult:
        with Vertical(id="create-char-dialog"):
            yield Label("Create Character", id="modal-title")

            yield Label("Name")
            yield Input(placeholder="Character name...", id="char-name")
            yield Label("Description")
            yield TextArea(id="char-description")

            yield Label(f"Attributes  (distribute {_POOL_TOTAL} points)", id="attr-label")
            yield Static(f"Remaining: {_POOL_TOTAL}", id="pool-display")
            yield PipSelector("Corpus", max_val=4, value=0, id="pip-corpus")
            yield PipSelector("Mens", max_val=4, value=0, id="pip-mens")
            yield PipSelector("Anima", max_val=4, value=0, id="pip-anima")

            yield Label("Personality  (rate each 1–5)", id="trait-label")
            yield PipSelector("Extraversion", min_val=1, max_val=_TRAIT_MAX, value=1, id="pip-extra")
            yield PipSelector("Openness", min_val=1, max_val=_TRAIT_MAX, value=1, id="pip-open")
            yield PipSelector("Agreeableness", min_val=1, max_val=_TRAIT_MAX, value=1, id="pip-agree")
            yield PipSelector("Neuroticism", min_val=1, max_val=_TRAIT_MAX, value=1, id="pip-neuro")
            yield PipSelector("Conscientiousness", min_val=1, max_val=_TRAIT_MAX, value=1, id="pip-consc")

            with Horizontal(id="modal-actions"):
                yield Button("Cancel", id="btn-cancel", variant="default")
                yield Button("Create", id="btn-create", variant="primary")

    def on_pip_selector_changed(self, event: PipSelector.Changed) -> None:
        if self._updating or event.selector.id not in _ATTR_IDS:
            return
        total = sum(self.query_one(f"#{pid}", PipSelector).value for pid in _ATTR_IDS)
        if total > _POOL_TOTAL:
            self._updating = True
            event.selector.value -= 1
            self._updating = False
            total = _POOL_TOTAL
        self.query_one("#pool-display", Static).update(f"Remaining: {_POOL_TOTAL - total}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-create":
            name = self.query_one("#char-name", Input).value.strip()
            if not name:
                return
            self.dismiss({
                "name": name,
                "description": self.query_one("#char-description", TextArea).text.strip(),
                "corpus": self.query_one("#pip-corpus", PipSelector).value,
                "mens": self.query_one("#pip-mens", PipSelector).value,
                "anima": self.query_one("#pip-anima", PipSelector).value,
                "extraversion": self.query_one("#pip-extra", PipSelector).value,
                "openness": self.query_one("#pip-open", PipSelector).value,
                "agreeableness": self.query_one("#pip-agree", PipSelector).value,
                "neuroticism": self.query_one("#pip-neuro", PipSelector).value,
                "conscientiousness": self.query_one("#pip-consc", PipSelector).value,
            })
            # TODO: CharacterService.create_character(**result)

    def action_dismiss_cancel(self) -> None:
        self.dismiss(None)
