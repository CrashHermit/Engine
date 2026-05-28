from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Label, RichLog
from textual.widgets import ContentSwitcher
from textual.containers import Horizontal, Vertical


class LeftPanel(Widget):
    """Switchable left panel: Scene log or Character info."""

    current_view: reactive[str] = reactive("scene")

    def compose(self) -> ComposeResult:
        with Horizontal(id="left-toggle"):
            yield Button("Scene", id="btn-scene", variant="primary")
            yield Button("Character", id="btn-character", variant="default")
        with ContentSwitcher(initial="scene", id="left-switcher"):
            yield RichLog(id="scene", min_width=0, wrap=True, markup=True, highlight=True)
            with Vertical(id="character"):
                yield Label("—", id="info-char-name")
                yield Label("—", id="info-location")

    def watch_current_view(self, view: str) -> None:
        self.query_one("#left-switcher", ContentSwitcher).current = view
        self.query_one("#btn-scene", Button).variant = "primary" if view == "scene" else "default"
        self.query_one("#btn-character", Button).variant = "primary" if view == "character" else "default"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in ("btn-scene", "btn-character"):
            self.current_view = event.button.id.removeprefix("btn-")
            event.stop()

    def write_scene(self, name: str, description: str, exits: str, entities: list[str] | None = None) -> None:
        entity_lines = ""
        if entities:
            lines = "\n".join(f"  · {e}" for e in entities)
            entity_lines = f"\n\n[dim]Entities:[/dim]\n[dim]{lines}[/dim]"
        self.query_one("#scene", RichLog).write(
            f"\n[bold #c9a84c]{name}[/bold #c9a84c]\n\n{description}{entity_lines}\n\n[dim]{exits}[/dim]"
        )

    def update_info(self, character_name: str, location_name: str) -> None:
        self.query_one("#info-char-name", Label).update(f"[bold]Character:[/bold] {character_name}")
        self.query_one("#info-location", Label).update(f"[bold]Location:[/bold] {location_name}")
