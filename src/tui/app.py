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
        self.push_screen(StartScreen())

    def action_help(self) -> None:
        pass  # TODO: push HelpModal


def main() -> None:
    EngineApp().run()


if __name__ == "__main__":
    main()
