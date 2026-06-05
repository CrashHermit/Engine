from __future__ import annotations

from src.worldgen.data import WorldData
from src.worldgen.stages.dungeon import DungeonStage
from src.worldgen.stages.grid import GridStage


class WorldgenPipeline:
    def __init__(self) -> None:
        self._grid_stage: GridStage = GridStage()
        self._dungeon_stage: DungeonStage = DungeonStage()

    def run(self, data: WorldData) -> WorldData:
        data = self._grid_stage.run(data=data)
        data = self._dungeon_stage.run(data=data)
        return data
