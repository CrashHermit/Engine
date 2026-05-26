from src.worldgen.data import WorldData


class WorldgenPipeline:
    def __init__(self, stages: list) -> None:
        self._stages: list = stages

    def run(self, data: WorldData) -> WorldData:
        for stage in self._stages:
            data = stage.run(data)
        return data
