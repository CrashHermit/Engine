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
        self._root_path: str = root_path
        self._root_password: str | None = root_password or os.getenv("ARCADEDB_ROOT_PASSWORD")
        self._http_port: int = http_port
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

    @property
    def root_path(self) -> str:
        return self._root_path

    @property
    def arcadedb_server(self) -> arcadedb.ArcadeDBServer:
        if self._server is None:
            raise RuntimeError("Server is not started")
        return self._server
