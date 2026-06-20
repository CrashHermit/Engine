from typing import Any

from textual import events
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static


class PipSelector(Static):
    """Render an arrow-key pip value selector.

    Displays ● ● ○ ○ ○ and responds to left/right arrow keys.
    """

    FILLED = "●"
    EMPTY = "○"
    can_focus = True

    value: reactive[int] = reactive(0)

    class Changed(Message):
        def __init__(self, selector: PipSelector, value: int) -> None:
            super().__init__()
            self.selector = selector
            self.value = value

    def __init__(
        self,
        label: str,
        min_val: int = 0,
        max_val: int = 5,
        value: int = 0,
        readonly: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__("", **kwargs)
        self._label = label
        self.min_val = min_val
        self.max_val = max_val
        self._initial_value = value
        self.readonly = readonly

    def on_mount(self) -> None:
        self.value = self._initial_value

    def watch_value(self, value: int) -> None:
        pips = " ".join(
            f"[bold #c9a84c]{self.FILLED}[/bold #c9a84c]"
            if i < value
            else f"[#6b5c7e]{self.EMPTY}[/#6b5c7e]"
            for i in range(self.max_val)
        )
        self.update(f"{self._label}: {pips}")

    def on_key(self, event: events.Key) -> None:
        if self.readonly:
            return
        if event.key == "right" and self.value < self.max_val:
            self.value += 1
            self.post_message(self.Changed(self, self.value))
            event.stop()
        elif event.key == "left" and self.value > self.min_val:
            self.value -= 1
            self.post_message(self.Changed(self, self.value))
            event.stop()
