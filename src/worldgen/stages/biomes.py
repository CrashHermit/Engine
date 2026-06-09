from __future__ import annotations

import math

from src.core.model.environment.climate.biome import BiomeEnum
from src.worldgen.config.worldgen_config import BiomeConfig
from src.worldgen.context import WorldContext
from src.worldgen.data import BiomeCenter, BiomeWeights


class BiomeStage:
    """Assigns soft biome weights per land cell from temperature and precipitation.

    Uses inverse-distance weighting from a list of biome ideal-climate
    centres so each cell can blend multiple neighbouring biomes.

    Pipeline position: after ``ClimateStage``.
    """

    def __init__(self, centers: list[BiomeCenter], config: BiomeConfig) -> None:
        self._centers = centers
        self._config = config

    def run(self, ctx: WorldContext) -> WorldContext:
        if ctx.data.mesh is None:
            return ctx
        cfg = self._config
        for cell in ctx.data.mesh.cells:
            if not cell.is_land or cell.is_lake:
                cell.biome_weights = []
                continue

            weights: dict[BiomeEnum, float] = {}
            total_weight = 0.0

            for center in self._centers:
                dx = cell.temperature - center.ideal_temp
                dy = cell.precipitation - center.ideal_precip
                distance = math.sqrt(dx**2 + dy**2)
                distance *= 1.0 + (cell.savagery * 0.15)
                distance *= 1.0 + (abs(cell.alignment) * 0.10)
                distance = max(0.001, distance)
                weight = 1.0 / (distance**cfg.blend_sharpness)
                weights[center.biome] = weight
                total_weight += weight

            normalized: dict[BiomeEnum, float] = {
                biome: (w / total_weight)
                for biome, w in weights.items()
                if (w / total_weight) > cfg.weight_cutoff
            }
            new_total = sum(normalized.values())

            if new_total > 0:
                cell.biome_weights = [
                    BiomeWeights(biome=biome, weight=(w / new_total))
                    for biome, w in normalized.items()
                ]
            else:
                top_biome = max(weights, key=weights.__getitem__)
                cell.biome_weights = [BiomeWeights(biome=top_biome, weight=1.0)]

        return ctx
