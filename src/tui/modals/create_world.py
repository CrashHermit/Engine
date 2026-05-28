import random

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, TextArea
from textual.containers import Horizontal, VerticalScroll
from src.services.world import WorldService


class CreateWorldModal(ModalScreen[dict[str, str] | None]):
    """Form for creating a new world (new ArcadeDB database)."""

    BINDINGS: list[BindingType] = [Binding(key="escape", action="dismiss_cancel", description="Cancel")]

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
            yield Label(content="Major blobs")
            yield Input(value="2", id="world-major-count")
            yield Label(content="Major radius %")
            yield Input(value="35", id="world-major-radius")
            yield Label(content="Detail blobs")
            yield Input(value="6", id="world-detail-count")
            yield Label(content="Detail radius %")
            yield Input(value="12", id="world-detail-radius")
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
            major_count: int = int(self.query_one("#world-major-count", Input).value.strip())
            major_radius_pct: int = int(self.query_one("#world-major-radius", Input).value.strip())
            detail_count: int = int(self.query_one("#world-detail-count", Input).value.strip())
            detail_radius_pct: int = int(self.query_one("#world-detail-radius", Input).value.strip())
        except ValueError:
            self.notify(message="Numeric fields must contain valid integers", severity="error")
            return

        try:
            WorldService(self.app.connection).create_world(
                name=name,
                description=description,
                seed=seed,
                size=size,
                major_count=major_count,
                major_radius_pct=major_radius_pct,
                detail_count=detail_count,
                detail_radius_pct=detail_radius_pct,
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
