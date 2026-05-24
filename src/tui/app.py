from textual.app import App, ComposeResult
from textual.binding import Binding

from .screens.start import StartScreen


class EngineApp(App):
    CSS_PATH = "theme.tcss"
    TITLE = "Dark Adventures"
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("f1", "help", "Help"),
    ]

    def on_mount(self) -> None:
        self.world_characters: dict[str, list[str]] = {}
        self.push_screen(StartScreen())

    def action_help(self) -> None:
        self.action_show_help_panel()
        # TODO: push HelpModal


def main() -> None:
    EngineApp().run()


if __name__ == "__main__":
    main()
