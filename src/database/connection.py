from pathlib import Path

import arcadedb_embedded as arcadedb

from src.database.server import Server


class DatabaseConnection:
    def __init__(self, server: Server) -> None:
        self._server: Server = server

    def _db_dir(self, name: str) -> Path:
        return Path(self._server.root_path) / "databases" / name

    def create_database(self, name: str) -> arcadedb.Database:
        if self._db_dir(name).exists():
            raise FileExistsError(f"Database {name!r} already exists")
        return self._server.arcadedb_server.create_database(name=name)

    def open_database(self, name: str) -> arcadedb.Database:
        if not self._db_dir(name).exists():
            raise FileNotFoundError(f"Database {name!r} does not exist")
        return self._server.arcadedb_server.get_database(name=name)

    def list_databases(self) -> list[str]:
        databases_dir = Path(self._server.root_path) / "databases"
        if not databases_dir.exists():
            return []
        return sorted(entry.name for entry in databases_dir.iterdir() if entry.is_dir())

    def delete_database(self, name: str) -> None:
        if not self._db_dir(name).exists():
            raise FileNotFoundError(f"Database {name!r} does not exist")
        self._server.remove_database(name)
