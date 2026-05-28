from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import Screen
from textual.widgets import Button, Label
from textual.containers import CenterMiddle, VerticalGroup
from src.tui.screens.world_list import WorldListScreen
from src.tui.modals.create_world import CreateWorldModal


class StartScreen(Screen):
    BINDINGS: list[BindingType] = [Binding(key="escape", action="app.quit", description="Quit")]

    def compose(self) -> ComposeResult:
        with CenterMiddle():
            with VerticalGroup(id="start-menu"):
                yield Label(content="DARK ADVENTURES", id="start-title")
                yield Button(label="Quick Start", id="btn-quick", variant="success")  # PROTOTYPE
                yield Button(label="Load World", id="btn-load", variant="primary")
                yield Button(label="New World", id="btn-new", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-quick":  # PROTOTYPE
            self._quick_start()  # PROTOTYPE
        elif event.button.id == "btn-load":
            self.app.push_screen(WorldListScreen())
        elif event.button.id == "btn-new":
            self.app.push_screen(CreateWorldModal(), callback=lambda result: self._on_dismiss(result))
    
    def _on_dismiss(self, result: dict[str, str] | None) -> None:
        if result:
            self.app.push_screen(WorldListScreen())

    # PROTOTYPE START
    def _quick_start(self) -> None:
        import arcadedb_embedded as arcadedb
        from src.database.schema import SchemaManager
        from src.database.repository.base import BaseRepository
        from src.database.repository.location import LocationRepository
        from src.database.repository.character import CharacterRepository
        from src.core.model.database import VertexType
        from src.tui.screens.game import GameScreen

        try:
            self.app.connection.delete_database("prototype")
        except Exception:
            pass

        db: arcadedb.Database = self.app.connection.create_database("prototype")
        SchemaManager(db).ensure()

        base = BaseRepository(db)
        location_repo = LocationRepository(base)
        character_repo = CharacterRepository(base)

        center = location_repo.create_start_location()
        character = base.create_vertex(
            type_name=VertexType.CHARACTER,
            name="Adventurer",
            description="A lone wanderer.",
        )
        character_repo.place_character(character, center)

        self.app.push_screen(GameScreen(character=character, database=db))
    # PROTOTYPE END
