import random

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, TextArea

from src.service.world import WorldService


class CreateWorldModal(ModalScreen[dict[str, str] | None]):
    """Form for creating a new world (new ArcadeDB database)."""

    BINDINGS: list[BindingType] = [
        Binding(key="escape", action="dismiss_cancel", description="Cancel")
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="create-world-dialog"):
            yield Label(content="Create New World", id="modal-title")
            yield Label(content="Name")
            yield Input(placeholder="World name...", id="world-name")
            yield Label(content="Description")
            yield TextArea(id="world-description")
            yield Label(content="Size (tiles per side)")
            yield Input(value="100", id="world-size")
            yield Label(content="Seed (blank for random)")
            yield Input(placeholder="e.g. 42", id="world-seed")
            yield Label(content="Biome")
            yield Input(value="Forest", id="world-biome")
            yield Label(content="Temperature")
            yield Input(value="20", id="world-temperature")
            yield Label(content="Precipitation")
            yield Input(value="100", id="world-precipitation")
            yield Label(content="Elevation")
            yield Input(value="100", id="world-elevation")
            with Horizontal(id="modal-actions"):
                yield Button(label="Cancel", id="btn-cancel", variant="default")
                yield Button(label="Create", id="btn-create", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(result=None)
            return

        if event.button.id != "btn-create":
            return

        name: str = self.query_one("#world-name", Input).value.strip()
        if not name:
            self.notify(message="World name is required", severity="error")
            return

        description: str = self.query_one("#world-description", TextArea).text.strip()
        seed_raw: str = self.query_one("#world-seed", Input).value.strip()

        try:
            seed: int = int(seed_raw) if seed_raw else random.randint(a=1, b=999_999)
            size: int = int(self.query_one("#world-size", Input).value.strip())
            biome: str = self.query_one("#world-biome", Input).value.strip()
            temperature: float = float(self.query_one("#world-temperature", Input).value.strip())
            precipitation: float = float(
                self.query_one("#world-precipitation", Input).value.strip()
            )
            elevation: float = float(self.query_one("#world-elevation", Input).value.strip())
        except ValueError:
            self.notify(message="Numeric fields must contain valid integers", severity="error")
            return

        try:
            WorldService(self.app.connection).create_world(
                name=name,
                description=description,
                seed=seed,
                size=size,
                biome=biome,
                temperature=temperature,
                precipitation=precipitation,
                elevation=elevation,
            )
        except FileExistsError:
            self.notify(message=f"World with '{name}' already exists")
            return
        except Exception as e:
            self.notify(message=f"Failed to create world: {e}", severity="error")
            return

        self.dismiss(result={"name": name, "description": description})

    def action_dismiss_cancel(self) -> None:
        self.dismiss(result=None)
