from textual.app import App
from textual.binding import Binding

from src.database.connection import DatabaseConnection
from src.database.server import Server
from src.service.checkpoint import CheckpointService
from src.service.factory import WorldSessionFactory
from src.tui.screens.start import StartScreen


class GameApp(App):
    ALLOW_SELECT = False

    CSS_PATH = "theme.tcss"
    TITLE = "Dark Adventures"
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("f1", "help", "Help"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.server: Server | None = None
        self.checkpoint: CheckpointService = CheckpointService()
        # Set once the async session worker finishes (see _init_session).
        self.factory: WorldSessionFactory | None = None

    def on_mount(self) -> None:
        self.server: Server = Server()
        self.server.start()
        self.connection: DatabaseConnection = DatabaseConnection(self.server)
        self.run_worker(self._init_session, exclusive=True)

    async def _init_session(self) -> None:
        await self.checkpoint.start()
        self.factory: WorldSessionFactory = WorldSessionFactory(
            self.connection,
            checkpointer=self.checkpoint.saver,
        )
        self.push_screen(StartScreen())

    def on_unmount(self) -> None:
        self.run_worker(self.checkpoint.stop, exclusive=True)
        if self.server:
            self.server.stop()

    def action_help(self) -> None:
        pass  # TODO: push HelpModal


def main() -> None:
    GameApp().run()


if __name__ == "__main__":
    main()
