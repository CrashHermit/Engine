import os
from pathlib import Path

import arcadedb_embedded as arcadedb
from dotenv import load_dotenv

load_dotenv()


class DatabaseConnection:
    def __init__(
        self,
        root_path: str = "data",
        root_password: str | None = None,
        http_port: int = 2480,
    ) -> None:
        self.root_path: str = root_path
        self.root_password: str | None = root_password or os.getenv("ARCADEDB_ROOT_PASSWORD")
        self.http_port: int = http_port
        self._server: arcadedb.ArcadeDBServer | None = None
        self._database: arcadedb.Database | None = None
        self._active_db_name: str | None = None

    def start_server(self) -> None:
        if self._server is not None:
            return
        Path(self.root_path).mkdir(parents=True, exist_ok=True)
        self._server = arcadedb.create_server(
            root_path=self.root_path,
            root_password=self.root_password,
            config={"http_port": self.http_port, "host": "localhost"},
        )
        self._server.start()

    def _release_database(self) -> None:
        if self._database is not None:
            self._database.close()
        self._database = None
        self._active_db_name = None

    @property
    def active_db_name(self) -> str | None:
        return self._active_db_name

    def use_database(self, db_name: str) -> arcadedb.Database:
        """Attach to an existing database. Raises if it does not exist."""
        if self._active_db_name == db_name and self._database is not None:
            return self._database

        if self._database is not None:
            self._release_database()

        if self._server is None:
            self.start_server()

        db_dir: Path = Path(self.root_path) / "databases" / db_name
        if not db_dir.exists():
            raise FileNotFoundError(
                f"Database {db_name!r} does not exist under {self.root_path}/databases"
            )

        self._database = self._server.get_database(name=db_name)
        self._active_db_name = db_name
        return self._database

    def create_database(self, db_name: str) -> arcadedb.Database:
        """Create a new database. Raises if it already exists."""
        if self._active_db_name == db_name and self._database is not None:
            return self._database

        if self._database is not None:
            self._release_database()

        if self._server is None:
            self.start_server()

        db_dir: Path = Path(self.root_path) / "databases" / db_name
        if db_dir.exists():
            raise FileExistsError(f"Database {db_name!r} already exists")

        self._database = self._server.create_database(name=db_name)
        self._active_db_name = db_name
        return self._database

    def switch_database(self, db_name: str) -> arcadedb.Database:
        """Release the current database and attach to an existing one."""
        self._release_database()
        return self.use_database(db_name)

    def detach_database(self) -> None:
        self._release_database()

    def shutdown_server(self) -> None:
        self._release_database()
        if self._server is not None:
            self._server.stop()
            self._server = None

    def open(self, db_name: str = "world") -> arcadedb.Database:
        """Start server (if needed) and attach; create the database if it does not exist."""
        db_dir: Path = Path(self.root_path) / "databases" / db_name
        if db_dir.exists():
            return self.use_database(db_name)
        return self.create_database(db_name)

    def close(self) -> None:
        """Stop server and release all handles."""
        self.shutdown_server()

    @classmethod
    def list_databases(cls, root_path: str = "data") -> list[str]:
        databases_dir: Path = Path(root_path) / "databases"
        if not databases_dir.exists():
            return []
        return sorted(entry.name for entry in databases_dir.iterdir() if entry.is_dir())

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
        self.start_server()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb) -> bool:
        self.shutdown_server()
        return False
