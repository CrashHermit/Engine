import arcadedb_embedded as arcadedb

from .connection import DatabaseConnection
from .schema import SchemaManager

class WorldStore:
    def __init__(self, db_name: str = "world", root_path: str = "data") -> None:
        self._connection: DatabaseConnection = DatabaseConnection(db_name=db_name, root_path=root_path)
        self._schema: SchemaManager | None = None

    def open(self) -> None:
        """Open DB and ensure schema. Call once at app startup."""
        self._connection.open()
        self._schema = SchemaManager(self._connection.database)
        self._schema.ensure()

    def close(self) -> None:
        """Close DB. Call on shutdown."""
        self._connection.close()
        self._schema = None

    @property
    def database(self) -> arcadedb.Database:
        return self._connection.database

    @property
    def studio_url(self) -> str:
        return self._connection.studio_url

    def __enter__(self) -> "WorldStore":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

if __name__ == "__main__":
    with WorldStore() as store:
        print("DB open:", store.database.get_name())