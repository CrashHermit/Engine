from textual.app import App
from textual.binding import Binding

from src.database.connection import DatabaseConnection
from src.database.server import Server
from src.tui.screens.start import StartScreen


class EngineApp(App):
    # Prevent click-drag from painting Textual selection regions over widgets.
    ALLOW_SELECT = False

    CSS_PATH = "theme.tcss"
    TITLE = "Dark Adventures"
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("f1", "help", "Help"),
    ]

    def on_mount(self) -> None:
        self.server = Server()
        self.server.start()
        self.connection = DatabaseConnection(self.server)
        self.world_characters: dict[str, list[str]] = {}
        self.world_character_data: dict[str, dict[str, dict]] = {}
        self.push_screen(StartScreen())

    def on_unmount(self) -> None:
        self.server.stop()

    def action_help(self) -> None:
        self.action_show_help_panel()
        # TODO: push HelpModal


def main() -> None:
    EngineApp().run()


if __name__ == "__main__":
    main()
