import uuid
from database.repository.user import UserRepository
from database.store import WorldStore
from database.repository.character import CharacterRepository

class Bootstrap:
    def __init__(self, store: WorldStore) -> None:
        self.store: WorldStore = store
        self.user_repo: UserRepository = UserRepository(self.store.database)
        self.character_repo: CharacterRepository = CharacterRepository(self.store.database)

    def bootstrap(self) -> None:
        self.user_repo.get_or_create_user()
