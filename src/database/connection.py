import os
from pathlib import Path
import arcadedb_embedded as arcadedb

from dotenv import load_dotenv

load_dotenv()


class DatabaseConnection:
    def __init__(
        self,
        db_name: str = "world",
        root_path: str = "data",
        root_password: str | None = None,
        http_port: int = 2480,
    ) -> None:
        self.db_name = db_name
        self.root_path = root_path
        self.root_password = root_password or os.getenv("ARCADEDB_ROOT_PASSWORD")
        self.http_port = http_port
        self._server: arcadedb.ArcadeDBServer | None = None
        self._database: arcadedb.Database | None = None

    def open(self) -> arcadedb.Database:
        Path(self.root_path).mkdir(parents=True, exist_ok=True)
        self._server = arcadedb.create_server(
            root_path=self.root_path,
            root_password=self.root_password,
            config={"http_port": self.http_port, "host": "localhost"},
        )
        self._server.start()
        db_dir = Path(self.root_path) / "databases" / self.db_name
        if db_dir.exists():
            self._database = self._server.get_database(self.db_name)
        else:
            self._database = self._server.create_database(self.db_name)
        return self._database

    def close(self) -> None:
        if self._server is not None:
            self._server.stop()
            self._server = None
            self._database = None

    @property
    def database(self) -> arcadedb.Database:
        if self._database is None:
            raise RuntimeError("Database is not open")
        return self._database

    @property
    def studio_url(self) -> str:
        if self._server is None:
            raise RuntimeError("Server is not started")
        return self._server.get_studio_url()

    def __enter__(self) -> "DatabaseConnection":
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
        return False