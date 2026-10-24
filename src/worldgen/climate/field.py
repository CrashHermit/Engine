"""Compose independently queryable, world-space climate fields."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.climate.circulation import CirculationField
from src.worldgen.climate.model import ClimateSample
from src.worldgen.climate.temperature import LatitudeTemperatureField


@dataclass(frozen=True, slots=True)
class ClimateField:
    """Prevailing circulation and latitude temperature around a shared axis."""

    circulation: CirculationField
    temperature: LatitudeTemperatureField

    def sample(self, positions: np.ndarray) -> ClimateSample:
        """Share axial values across circulation and temperature evaluation."""
        circulation = self.circulation.sample(positions)
        temperature = self.temperature.sample_from_axis(circulation.axial_coordinate)
        return ClimateSample(circulation, temperature)
