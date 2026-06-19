from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static, TextArea

from src.tui.widgets.value_stepper import ValueStepper

_POOL_TOTAL: int = 5
_ATTR_IDS: tuple[str, str, str] = ("step-corpus", "step-mens", "step-anima")


class CreateCharacterModal(ModalScreen[dict[str, int | str] | None]):
    """Build a character-creation form with an attribute pool."""

    BINDINGS: list[BindingType] = [
        Binding(key="escape", action="dismiss_cancel", description="Cancel")
    ]

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

            with Vertical(id="char-attributes-section"):
                yield Label(
                    content=f"Attributes  (distribute {_POOL_TOTAL} points)",
                    id="attr-label",
                )
                yield Static(content=f"Remaining: {_POOL_TOTAL}", id="pool-display")
                yield ValueStepper(
                    label="Corpus", min_val=0, max_val=4, value=0, id="step-corpus"
                )
                yield ValueStepper(
                    label="Mens", min_val=0, max_val=4, value=0, id="step-mens"
                )
                yield ValueStepper(
                    label="Anima", min_val=0, max_val=4, value=0, id="step-anima"
                )

            with Vertical(id="char-body-section"):
                yield Label(content="Body Parts", id="body-label")
                yield ValueStepper(
                    label="Manipulator",
                    min_val=0,
                    max_val=4,
                    value=0,
                    id="step-manipulator",
                )
                yield ValueStepper(
                    label="Movement", min_val=0, max_val=4, value=0, id="step-movement"
                )
                yield ValueStepper(
                    label="Sense", min_val=0, max_val=4, value=0, id="step-storage"
                )

            with Horizontal(id="modal-actions"):
                yield Button(label="Cancel", id="btn-cancel", variant="default")
                yield Button(label="Create", id="btn-create", variant="primary")

    def on_value_stepper_changed(self, event: ValueStepper.Changed) -> None:
        if self._updating or event.stepper.id not in _ATTR_IDS:
            return
        total: int = sum(
            self.query_one(f"#{pid}", ValueStepper).value for pid in _ATTR_IDS
        )
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
            self.dismiss(
                result={
                    "name": name,
                    "description": self.query_one(
                        "#char-description", TextArea
                    ).text.strip(),
                    "corpus": self.query_one("#step-corpus", ValueStepper).value,
                    "mens": self.query_one("#step-mens", ValueStepper).value,
                    "anima": self.query_one("#step-anima", ValueStepper).value,
                }
            )

    def action_dismiss_cancel(self) -> None:
        self.dismiss(result=None)
