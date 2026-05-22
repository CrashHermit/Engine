from pathlib import Path

import arcadedb_embedded as arcadedb

from .connection import DatabaseConnection
from .schema import SchemaManager

class WorldStore:
    def __init__(self, path: Path = Path("data/world")) -> None:
        self._connection: DatabaseConnection = DatabaseConnection(path)
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

    def __enter__(self) -> "WorldStore":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

if __name__ == "__main__":
    with WorldStore() as store:
        print("DB open:", store.database.get_name())