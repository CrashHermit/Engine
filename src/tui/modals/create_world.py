from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, TextArea
from textual.containers import Horizontal, Vertical


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
            with Horizontal(id="modal-actions"):
                yield Button("Cancel", id="btn-cancel", variant="default")
                yield Button("Create", id="btn-create", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-create":
            name = self.query_one("#world-name", Input).value.strip()
            if not name:
                return
            description = self.query_one("#world-description", TextArea).text.strip()
            self.dismiss({"name": name, "description": description})
            # TODO: WorldStore(db_name=name).open() and Bootstrap().bootstrap()

    def action_dismiss_cancel(self) -> None:
        self.dismiss(None)
