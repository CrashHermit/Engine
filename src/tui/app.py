from textual.app import App
from textual.binding import Binding

from src.database.connection import DatabaseConnection
from src.database.server import Server
from src.tui.screens.start import StartScreen


class GameApp(App):
    ALLOW_SELECT = False

    CSS_PATH = [
        "theme/base.tcss",
        "theme/screens.tcss",
        "theme/widgets.tcss",
        "theme/modals.tcss",
    ]
    TITLE = "Dark Adventures"
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("f1", "help", "Help"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.server: Server | None = None

    def on_mount(self) -> None:
        self.server: Server = Server()
        self.server.start()
        self.connection: DatabaseConnection = DatabaseConnection(self.server)
        self.push_screen(StartScreen())

    def on_unmount(self) -> None:
        if self.server:
            self.server.stop()

    def action_help(self) -> None:
        pass  # TODO: push HelpModal


def main() -> None:
    GameApp().run()


if __name__ == "__main__":
    main()
