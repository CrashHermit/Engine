"""Configuration for independent continuous climate components."""

from dataclasses import dataclass, field

from src.worldgen.climate.circulation import CirculationConfig
from src.worldgen.climate.temperature import TemperatureConfig


@dataclass(frozen=True, slots=True)
class ClimateConfig:
    """Top-level climate settings."""

    circulation: CirculationConfig = field(default_factory=CirculationConfig)
    temperature: TemperatureConfig = field(default_factory=TemperatureConfig)
