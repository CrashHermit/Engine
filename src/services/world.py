from bootstrap import Bootstrap
from database.repository.location import LocationRepository
from database.store import WorldStore
from services.world_builder import WorldBuilderService


class WorldService:
    def create_world(self, name: str, width: int, height: int) -> WorldStore:
        store = WorldStore(db_name=name)
        store.open()
        Bootstrap(store).bootstrap()
        WorldBuilderService(LocationRepository(store.database)).build_world(
            width=width, height=height
        )
        return store
