from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static, TextArea
from textual.containers import Horizontal, Vertical, VerticalScroll

from src.tui.widgets.value_stepper import ValueStepper

# Unified 0–4 "dot" scale for the whole sheet (decision #20): attributes are the
# dice ratings, traits are flavor/steering signal — both 0–4.
_POOL_TOTAL: int = 4
_TRAIT_MAX: int = 4
_TRAIT_DEFAULT: int = 2
_ATTR_IDS: tuple[str, str, str] = ("step-corpus", "step-mens", "step-anima")


class CreateCharacterModal(ModalScreen[dict[str, int | str] | None]):
    """Form for creating a new character with attribute pool and personality ratings."""

    BINDINGS: list[BindingType] = [Binding(key="escape", action="dismiss_cancel", description="Cancel")]

    def __init__(self) -> None:
        super().__init__()
        self._updating: bool = False

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="create-char-dialog"):
            yield Label(content="Create Character", id="modal-title")

            yield Label(content="Name")
            yield Input(placeholder="Character name...", id="char-name")
            yield Label(content="Description")
            yield TextArea(id="char-description")
            yield Label(content="Vice  (a freeform indulgence — your relief)")
            yield Input(placeholder="e.g. cheap wine, old grudges...", id="char-vice")

            with Vertical(id="char-attributes-section"):
                yield Label(content=f"Attributes  (distribute {_POOL_TOTAL} points)", id="attr-label")
                yield Static(content=f"Remaining: {_POOL_TOTAL}", id="pool-display")
                yield ValueStepper(label="Corpus", min_val=0, max_val=4, value=0, id="step-corpus")
                yield ValueStepper(label="Mens", min_val=0, max_val=4, value=0, id="step-mens")
                yield ValueStepper(label="Anima", min_val=0, max_val=4, value=0, id="step-anima")

            with Vertical(id="char-personality-section"):
                yield Label(content="Personality  (rate each 0–4)", id="trait-label")
                yield ValueStepper(label="Extraversion", min_val=0, max_val=_TRAIT_MAX, value=_TRAIT_DEFAULT, id="step-extra")
                yield ValueStepper(label="Openness", min_val=0, max_val=_TRAIT_MAX, value=_TRAIT_DEFAULT, id="step-open")
                yield ValueStepper(label="Agreeableness", min_val=0, max_val=_TRAIT_MAX, value=_TRAIT_DEFAULT, id="step-agree")
                yield ValueStepper(label="Neuroticism", min_val=0, max_val=_TRAIT_MAX, value=_TRAIT_DEFAULT, id="step-neuro")
                yield ValueStepper(label="Conscientiousness", min_val=0, max_val=_TRAIT_MAX, value=_TRAIT_DEFAULT, id="step-consc")

            with Horizontal(id="modal-actions"):
                yield Button(label="Cancel", id="btn-cancel", variant="default")
                yield Button(label="Create", id="btn-create", variant="primary")

    def on_value_stepper_changed(self, event: ValueStepper.Changed) -> None:
        if self._updating or event.stepper.id not in _ATTR_IDS:
            return
        total: int = sum(self.query_one(f"#{pid}", ValueStepper).value for pid in _ATTR_IDS)
        if total > _POOL_TOTAL:
            self._updating = True
            event.stepper.value -= 1
            self._updating = False
            total: int = _POOL_TOTAL
        self.query_one("#pool-display", Static).update(
            content=f"Remaining: {_POOL_TOTAL - total}"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(result=None)
        elif event.button.id == "btn-create":
            name: str = self.query_one("#char-name", Input).value.strip()
            if not name:
                return
            self.dismiss(result={
                "name": name,
                "description": self.query_one("#char-description", TextArea).text.strip(),
                "vice": self.query_one("#char-vice", Input).value.strip(),
                "corpus": self.query_one("#step-corpus", ValueStepper).value,
                "mens": self.query_one("#step-mens", ValueStepper).value,
                "anima": self.query_one("#step-anima", ValueStepper).value,
                "extraversion": self.query_one("#step-extra", ValueStepper).value,
                "openness": self.query_one("#step-open", ValueStepper).value,
                "agreeableness": self.query_one("#step-agree", ValueStepper).value,
                "neuroticism": self.query_one("#step-neuro", ValueStepper).value,
                "conscientiousness": self.query_one("#step-consc", ValueStepper).value,
            })

            

    def action_dismiss_cancel(self) -> None:
        self.dismiss(result=None)
