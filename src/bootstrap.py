from datetime import datetime, timezone
from database.repository.base import BaseRepository
from database.repository.user import UserRepository
from database.store import WorldStore

class Bootstrap:
    def __init__(self, store: WorldStore) -> None:
        self.store: WorldStore = store
        self.user_repo: UserRepository = UserRepository(self.store.database)

    def bootstrap(self) -> None:
        pass