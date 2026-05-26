import random

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, TextArea
from textual.containers import Horizontal, Vertical

from services.world import WorldService


class CreateWorldModal(ModalScreen[dict[str, str] | None]):
    """Form for creating a new world (new ArcadeDB database)."""

    BINDINGS = [Binding("escape", "dismiss_cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="create-world-dialog"):
            yield Label("Create New World", id="modal-title")
            yield Label("Name")
            yield Input(placeholder="World name...", id="world-name")
            yield Label("Description")
            yield TextArea(id="world-description")
            yield Label("Size (tiles per side)")
            yield Input(value="100", id="world-size")
            yield Label("Seed (blank for random)")
            yield Input(placeholder="e.g. 42", id="world-seed")
            yield Label("Major blobs")
            yield Input(value="2", id="world-major-count")
            yield Label("Major radius %")
            yield Input(value="35", id="world-major-radius")
            yield Label("Detail blobs")
            yield Input(value="6", id="world-detail-count")
            yield Label("Detail radius %")
            yield Input(value="12", id="world-detail-radius")
            with Horizontal(id="modal-actions"):
                yield Button("Cancel", id="btn-cancel", variant="default")
                yield Button("Create", id="btn-create", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-create":
            name: str = self.query_one("#world-name", Input).value.strip()
            if not name:
                return
            description: str = self.query_one("#world-description", TextArea).text.strip()
            seed_raw: str = self.query_one("#world-seed", Input).value.strip()
            seed: int = int(seed_raw) if seed_raw else random.randint(1, 999_999)
            size: int = int(self.query_one("#world-size", Input).value.strip())
            major_count: int = int(self.query_one("#world-major-count", Input).value.strip())
            major_radius_pct: int = int(self.query_one("#world-major-radius", Input).value.strip())
            detail_count: int = int(self.query_one("#world-detail-count", Input).value.strip())
            detail_radius_pct: int = int(self.query_one("#world-detail-radius", Input).value.strip())

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

            self.dismiss({"name": name, "description": description})

    def action_dismiss_cancel(self) -> None:
        self.dismiss(None)
