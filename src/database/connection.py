import os
from pathlib import Path
import arcadedb_embedded as arcadedb

from dotenv import load_dotenv

load_dotenv()

class DatabaseConnection:
    def __init__(self, path: Path = Path("data/world")) -> None:
        self.path: Path = path
        self._database: arcadedb.Database | None = None

    def create(self) -> arcadedb.Database:
        self.path.mkdir(parents=True, exist_ok=True)
        if any(self.path.iterdir()):
            self._database = arcadedb.open_database(path=str(self.path))
        else:
            self._database = arcadedb.create_database(path=str(self.path))
        self._database = arcadedb.create_database(path=str(self.path))
        return self._database

    def open(self) -> arcadedb.Database:
        self._database = arcadedb.open_database(path=str(self.path))
        return self._database

    def close(self) -> None:
        if self._database is not None:
            self._database.close()
            self._database = None

    @property
    def database(self) -> arcadedb.Database:
        if self._database is None:
            raise RuntimeError("Database is not open")
        return self._database

    def __enter__(self) -> "DatabaseConnection":
        self.create()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
        return False