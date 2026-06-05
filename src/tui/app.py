from __future__ import annotations

from textual.app import App
from textual.binding import Binding

from src.bootstrap import AppBootstrap
from src.logging_utils import configure_logging
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
        configure_logging()
        # Composition root lives in src/bootstrap so the TUI never imports
        # src/database directly. Screens read `self.app.bootstrap.connection`
        # and `self.app.bootstrap.factory`.
        self.bootstrap: AppBootstrap = AppBootstrap()

    def on_mount(self) -> None:
        self.bootstrap.start_server()
        self.run_worker(self._init_session, exclusive=True)

    async def _init_session(self) -> None:
        await self.bootstrap.start_session()
        self.push_screen(StartScreen())

    def on_unmount(self) -> None:
        self.run_worker(self.bootstrap.stop, exclusive=True)

    def action_help(self) -> None:
        pass  # TODO: push HelpModal


def main() -> None:
    GameApp().run()


if __name__ == "__main__":
    main()
