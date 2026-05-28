from rich.markup import escape
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Button, Input, RichLog, Label
from textual.containers import Vertical, Horizontal


class ChatPanel(Widget):
    """Single chat panel with IC/OOC channel toggle."""

    channel: reactive[str] = reactive("ic")

    class MessageSent(Message):
        def __init__(self, text: str, channel: str) -> None:
            super().__init__()
            self.text = text
            self.channel = channel

    def compose(self) -> ComposeResult:
        with Vertical(id="chat-layout"):
            with Horizontal(id="channel-toggle"):
                yield Label("Channel:", id="channel-label")
                yield Button("IC", id="btn-ic", variant="primary")
                yield Button("OOC", id="btn-ooc", variant="default")
            yield RichLog(id="chat-log", highlight=True, markup=True, wrap=True)
            with Horizontal(id="input-bar"):
                yield Input(placeholder="Type your message...", id="msg-input")
                yield Button("Send", id="btn-send", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ic":
            self.channel = "ic"
        elif event.button.id == "btn-ooc":
            self.channel = "ooc"
        elif event.button.id == "btn-send":
            self._send_message()
        event.stop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._send_message()
        event.stop()

    def watch_channel(self, channel: str) -> None:
        self.query_one("#btn-ic", Button).variant = "primary" if channel == "ic" else "default"
        self.query_one("#btn-ooc", Button).variant = "primary" if channel == "ooc" else "default"

    def _send_message(self) -> None:
        input_widget = self.query_one("#msg-input", Input)
        text = input_widget.value.strip()
        if not text:
            return
        log = self.query_one("#chat-log", RichLog)
        tag = "[bold #c9a84c]IC[/bold #c9a84c]" if self.channel == "ic" else "[bold #7ec8e3]OOC[/bold #7ec8e3]"
        log.write(f"{tag} [bold]You:[/bold] {escape(text)}")
        input_widget.value = ""
        self.post_message(self.MessageSent(text, self.channel))
