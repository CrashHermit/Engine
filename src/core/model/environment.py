from __future__ import annotations

from dataclasses import dataclass
from src.core.model.climate import ClimateData
from src.core.model.terrain import TerrainData


@dataclass
class EnvironmentData:
    climate: ClimateData
    terrain: TerrainData