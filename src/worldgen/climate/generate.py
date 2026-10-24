"""Construct deterministic world-space climate fields."""

from src.worldgen.climate.circulation import (
    CirculationBandField,
    CirculationConfig,
    CirculationField,
    ZonalWindField,
)
from src.worldgen.climate.config import ClimateConfig
from src.worldgen.climate.field import ClimateField
from src.worldgen.climate.temperature import LatitudeTemperatureField
from src.worldgen.field.axis import AxialCoordinateField
from src.worldgen.field.motion import RotationField


def generate_circulation_field(
    config: CirculationConfig,
    axis_direction: tuple[float, float, float],
) -> CirculationField:
    """Build a zonal circulation field around the explicit axial direction."""
    axis = AxialCoordinateField(axis_direction)
    bands = CirculationBandField(axis)
    wind = ZonalWindField(
        rotation=RotationField(axis.direction),
        bands=bands,
        base_speed_m_s=config.base_speed_m_s,
        axis_calm_radius=config.axis_calm_radius_percent / 100.0,
    )
    return CirculationField(axis=axis, bands=bands, wind=wind)


def generate_climate_field(
    config: ClimateConfig, axis_direction: tuple[float, float, float]
) -> ClimateField:
    """Compose circulation and temperature using one normalized planetary axis."""
    circulation = generate_circulation_field(config.circulation, axis_direction)
    temperature = LatitudeTemperatureField(circulation.axis, config.temperature)
    return ClimateField(circulation, temperature)
