from typing import Any

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static


class ValueStepper(Widget):
    """Label + [-] value [+] row. Styles live in theme.tcss (custom $da-* vars)."""

    value: reactive[int] = reactive(0)

    class Changed(Message):
        def __init__(self, stepper: "ValueStepper", new_value: int) -> None:
            super().__init__()
            self.stepper: ValueStepper = stepper
            self.new_value: int = new_value

    def __init__(
        self,
        label: str,
        min_val: int = 0,
        max_val: int = 5,
        value: int = 0,
        readonly: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._label: str = label
        self.min_val: int = min_val
        self.max_val: int = max_val
        self._initial_value: int = value
        self.readonly: bool = readonly

    def compose(self) -> ComposeResult:
        yield Label(content=self._label, classes="stepper-label")
        with Horizontal(classes="stepper-controls"):
            yield Static(content="-", id="btn-dec", classes="stepper-button")
            yield Static(
                content=str(self._initial_value), id="stepper-value", classes="stepper-value"
            )
            yield Static(content="+", id="btn-inc", classes="stepper-button")

    def on_mount(self) -> None:
        self.value = self._initial_value
        if self.readonly:
            self.query_one("#btn-dec", Static).add_class("-disabled")
            self.query_one("#btn-inc", Static).add_class("-disabled")

    def watch_value(self, value: int) -> None:
        self.query_one("#stepper-value", Static).update(content=str(value))

    def on_click(self, event: events.Click) -> None:
        if self.readonly:
            return

        clicked_id: str | None = event.widget.id if event.widget is not None else None
        if clicked_id not in ("btn-dec", "btn-inc"):
            return

        if clicked_id == "btn-dec" and self.value > self.min_val:
            self.value -= 1
            self.post_message(self.Changed(self, self.value))
        elif clicked_id == "btn-inc" and self.value < self.max_val:
            self.value += 1
            self.post_message(self.Changed(self, self.value))
        event.stop()
