from typing import Any

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, RichLog


class ChatPanel(Widget):
    """Render a single chat panel."""

    class MessageSent(Message):
        def __init__(self, text: str) -> None:
            super().__init__()
            self.text: str = text

    def __init__(self, character_name: str = "You", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._character_name: str = character_name

    def compose(self) -> ComposeResult:
        with Vertical(id="chat-layout"):
            yield RichLog(
                id="chat-log", min_width=0, wrap=True, markup=True, highlight=True
            )
            with Horizontal(id="input-bar"):
                yield Input(placeholder="Type your message...", id="msg-input")
                yield Button(label="Send", id="btn-send", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-send":
            self._send_message()
        event.stop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._send_message()
        event.stop()

    def set_processing(self, active: bool) -> None:
        input_widget = self.query_one("#msg-input", Input)
        btn = self.query_one("#btn-send", Button)
        input_widget.disabled = active
        btn.disabled = active

    def _send_message(self) -> None:
        input_widget = self.query_one("#msg-input", Input)
        if input_widget.disabled:
            return
        text = input_widget.value.strip()
        if not text:
            return
        log = self.query_one("#chat-log", RichLog)
        log.write(
            f"[bold #a0bfdf]{escape(self._character_name)}:[/bold #a0bfdf]"
            f" {escape(text)}"
        )
        input_widget.value = ""
        self.post_message(self.MessageSent(text))
