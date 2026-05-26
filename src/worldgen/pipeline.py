from src.worldgen.data import WorldData
from src.worldgen.stages.grid import GridStage


class WorldgenPipeline:
    def __init__(self) -> None:
        self._grid_stage: GridStage = GridStage()

    def run(self, data: WorldData) -> WorldData:
        data: WorldData = self._grid_stage.run(data=data)

        return data
