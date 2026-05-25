import os
from pathlib import Path

import arcadedb_embedded as arcadedb
from dotenv import load_dotenv

load_dotenv()


class Server:
    def __init__(
        self,
        root_path: str = "data",
        root_password: str | None = None,
        http_port: int = 2480,
    ) -> None:
        self._root_path = root_path
        self._root_password = root_password or os.getenv("ARCADEDB_ROOT_PASSWORD")
        self._http_port = http_port
        self._server: arcadedb.ArcadeDBServer | None = None

    def start(self) -> None:
        if self._server is not None:
            return
        Path(self._root_path).mkdir(parents=True, exist_ok=True)
        self._server = arcadedb.create_server(
            root_path=self._root_path,
            root_password=self._root_password,
            config={"http_port": self._http_port, "host": "localhost"},
        )
        self._server.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.stop()
            self._server = None

    def create_database(self, name: str) -> arcadedb.Database:
        if self._server is None:
            raise RuntimeError("Server is not started")
        db_dir = Path(self._root_path) / "databases" / name
        if db_dir.exists():
            raise FileExistsError(f"Database {name!r} already exists")
        return self._server.create_database(name=name)

    def open_database(self, name: str) -> arcadedb.Database:
        if self._server is None:
            raise RuntimeError("Server is not started")
        db_dir = Path(self._root_path) / "databases" / name
        if not db_dir.exists():
            raise FileNotFoundError(f"Database {name!r} does not exist")
        return self._server.get_database(name=name)

    def list_databases(self) -> list[str]:
        databases_dir = Path(self._root_path) / "databases"
        if not databases_dir.exists():
            return []
        return sorted(entry.name for entry in databases_dir.iterdir() if entry.is_dir())
