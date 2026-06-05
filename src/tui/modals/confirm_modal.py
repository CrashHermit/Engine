from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmModal(ModalScreen[bool]):
    """Display a generic yes/no confirmation dialog."""

    BINDINGS: list[BindingType] = [
        Binding(key="escape", action="dismiss_cancel", description="Cancel"),
    ]

    def __init__(
        self,
        *,
        title: str,
        message: str,
        confirm_label: str = "Delete",
    ) -> None:
        super().__init__()
        self._title = title
        self._message = message
        self._confirm_label = confirm_label

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Label(content=self._title, id="modal-title")
            yield Label(content=self._message, id="confirm-message")
            with Horizontal(id="modal-actions"):
                yield Button(label="Cancel", id="btn-cancel", variant="default")
                yield Button(
                    label=self._confirm_label, id="btn-confirm", variant="error"
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(result=False)
            return
        if event.button.id == "btn-confirm":
            self.dismiss(result=True)

    def action_dismiss_cancel(self) -> None:
        self.dismiss(result=False)


class ConfirmDeleteWorldModal(ConfirmModal):
    def __init__(self, *, world_name: str) -> None:
        super().__init__(
            title="Delete World?",
            message=(
                f'Are you sure you want to delete the world "{world_name}"?'
                " This cannot be undone."
            ),
        )
