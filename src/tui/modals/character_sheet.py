from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from src.core.model.character import CharacterData
from src.tui.widgets.pip_selector import PipSelector


class CharacterSheetModal(ModalScreen[None]):
    """Display a read-only character sheet for the active character."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("c", "dismiss", "Close"),
    ]

    def __init__(self, character: CharacterData) -> None:
        super().__init__()
        self._character = character

    def compose(self) -> ComposeResult:
        with Vertical(id="character-sheet"):
            yield Label("CHARACTER SHEET", id="sheet-title")

            with Horizontal(id="sheet-identity"):
                with Vertical(id="sheet-left"):
                    yield Label("", id="sheet-name")
                    yield Static("", id="sheet-description")
                with Vertical(id="sheet-right"):
                    yield Label("Attributes", id="attrs-title")
                    yield PipSelector(
                        "Corpus", max_val=4, value=0, readonly=True, id="pip-corpus"
                    )
                    yield PipSelector(
                        "Mens", max_val=4, value=0, readonly=True, id="pip-mens"
                    )
                    yield PipSelector(
                        "Anima", max_val=4, value=0, readonly=True, id="pip-anima"
                    )

            yield Label("Condition", id="condition-title")
            yield Static("", id="sheet-condition")

            yield Label("Equipment", id="equipment-title")
            yield Static("—", id="sheet-equipment")

            yield Label("Inventory", id="inventory-title")
            yield Static("—", id="sheet-inventory")

            yield Button("Close", id="btn-close", variant="default")

    def on_mount(self) -> None:
        self.query_one("#sheet-name", Label).update(self._character.name or "—")
        self.query_one("#sheet-description", Static).update(
            self._character.description or ""
        )

        self.query_one("#sheet-condition", Static).update(
            f"Stress: {self._character.stress} / {self._character.stress_max}"
            f"  |  Trauma: {self._character.trauma} / {self._character.trauma_max}"
        )

        self.query_one("#pip-corpus", PipSelector).value = self._character.corpus
        self.query_one("#pip-mens", PipSelector).value = self._character.mens
        self.query_one("#pip-anima", PipSelector).value = self._character.anima

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close":
            self.dismiss()
