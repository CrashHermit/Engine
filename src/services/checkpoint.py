from pathlib import Path
from typing import TYPE_CHECKING

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class CheckpointService:
    def __init__(self, db_path: str | Path = "data/checkpointers.sqlite") -> None:
        self._db_path = Path(db_path)
        self._cm: AsyncIterator[AsyncSqliteSaver] | None = None
        self.saver: BaseCheckpointSaver | None = None

    async def start(self) -> BaseCheckpointSaver:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._cm = AsyncSqliteSaver.from_conn_string(str(self._db_path))
        self.saver = await self._cm.__aenter__()
        return self.saver

    async def stop(self) -> None:
        if self._cm is not None:
            await self._cm.__aexit__(None, None, None)
        self._cm = None
        self.saver = None
