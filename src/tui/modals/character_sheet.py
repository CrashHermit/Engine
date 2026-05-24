from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual.containers import Horizontal, Vertical

from ..widgets.pip_selector import PipSelector


class CharacterSheetModal(ModalScreen):
    """Full-screen character sheet: stats, equipment, inventory, personality."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("c", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="character-sheet"):
            yield Label("CHARACTER SHEET", id="sheet-title")

            with Horizontal(id="sheet-identity"):
                with Vertical(id="sheet-left"):
                    yield Label("Aldric the Bold", id="sheet-name")
                    yield Static(
                        "A seasoned warrior from the northern provinces. "
                        "Scarred but unbroken, he carries the weight of a dozen campaigns.",
                        id="sheet-description",
                    )
                with Vertical(id="sheet-right"):
                    yield Label("Attributes", id="attrs-title")
                    yield PipSelector("Corpus", max_val=4, value=2, readonly=True)
                    yield PipSelector("Mens", max_val=4, value=1, readonly=True)
                    yield PipSelector("Anima", max_val=4, value=2, readonly=True)

            yield Label("Condition", id="condition-title")
            yield Static(
                "HP: 10 / 10  |  Wounds: None  |  Status: Healthy",
                id="sheet-condition",
            )

            yield Label("Equipment", id="equipment-title")
            yield Static(
                "Longsword (1d8+2)  |  Shield (+2 AC)  |  Chain Mail (AC 14)  |  Torch  |  Rations ×3",
                id="sheet-equipment",
            )

            yield Label("Inventory", id="inventory-title")
            yield Static(
                "50 gold  |  Healing Potion  |  Rope (50ft)  |  Flint & Steel",
                id="sheet-inventory",
            )

            yield Label("Personality", id="personality-title")
            with Horizontal(id="personality-traits"):
                yield PipSelector("Extraversion", min_val=1, max_val=5, value=3, readonly=True)
                yield PipSelector("Openness", min_val=1, max_val=5, value=4, readonly=True)
                yield PipSelector("Agreeableness", min_val=1, max_val=5, value=2, readonly=True)
                yield PipSelector("Neuroticism", min_val=1, max_val=5, value=3, readonly=True)
                yield PipSelector("Conscientiousness", min_val=1, max_val=5, value=4, readonly=True)

            yield Button("Close", id="btn-close", variant="default")
            # TODO: populate from CharacterRepository for the active character

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close":
            self.dismiss()
