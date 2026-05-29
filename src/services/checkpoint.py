from pathlib import Path

class CheckpointService:
    def __init__(self, db_path: str | Path = "data/checkpointers.sqlite") -> None:
        pass

    async def start(self) -> BaseCheckpointSaver:
        pass

    async def stop(self) -> None:
        pass

    