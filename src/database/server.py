import os
from pathlib import Path

import arcadedb_embedded as arcadedb
from arcadedb_embedded.exceptions import ArcadeDBError
from dotenv import load_dotenv

load_dotenv()

_LOCK_ERROR_MARKERS = ("LockException", "locked by another process")


class Server:
    def __init__(
        self,
        root_path: str = "data",
        root_password: str | None = None,
        http_port: int = 2480,
    ) -> None:
        self._root_path: str = root_path
        self._root_password: str | None = root_password or os.getenv("ARCADEDB_ROOT_PASSWORD")
        self._http_port: int = http_port
        self._server: arcadedb.ArcadeDBServer | None = None

    def _create_server(self) -> arcadedb.ArcadeDBServer:
        server = arcadedb.create_server(
            root_path=self._root_path,
            root_password=self._root_password,
            config={"http_port": self._http_port, "host": "localhost"},
        )
        server.start()
        return server

    def _try_clear_stale_locks(self) -> bool:
        databases_path = Path(self._root_path) / "databases"
        if not databases_path.exists():
            return False
        cleared = False
        for lock_file in databases_path.rglob(".lock"):
            try:
                lock_file.unlink()
                cleared = True
            except OSError:
                pass
        return cleared

    def start(self) -> None:
        if self._server is not None:
            return
        Path(self._root_path).mkdir(parents=True, exist_ok=True)
        try:
            self._server = self._create_server()
        except ArcadeDBError as e:
            if not any(m in str(e) for m in _LOCK_ERROR_MARKERS):
                raise
            if self._try_clear_stale_locks():
                self._server = self._create_server()
            else:
                raise ArcadeDBError(
                    "A database is locked by another running process. "
                    "Close any other instances of the application (or kill lingering java processes) and try again."
                ) from e

    def stop(self) -> None:
        if self._server is not None:
            self._server.stop()
            self._server = None

    @property
    def root_path(self) -> str:
        return self._root_path

    @property
    def arcadedb_server(self) -> arcadedb.ArcadeDBServer:
        if self._server is None:
            raise RuntimeError("Server is not started")
        return self._server
