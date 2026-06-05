from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, TextArea

from src.service.world import WorldService


class CreateWorldModal(ModalScreen[dict[str, str] | None]):
    """Provide a form for creating a new world (new ArcadeDB database)."""

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

        try:
            size: int = int(self.query_one("#world-size", Input).value.strip())
        except ValueError:
            self.notify(message="Size must be a valid integer", severity="error")
            return

        try:
            WorldService(self.app.bootstrap.connection).create_world(
                name=name,
                description=description,
                size=size,
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
