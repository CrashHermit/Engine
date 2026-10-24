"""Immutable sampled climate quantities."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class CirculationSample:
    """Zonal coordinate, band strength, and Cartesian wind at query points."""

    axial_coordinate: np.ndarray
    band_strength: np.ndarray
    wind_vectors_m_s: np.ndarray

    def __post_init__(self) -> None:
        self.axial_coordinate.setflags(write=False)
        self.band_strength.setflags(write=False)
        self.wind_vectors_m_s.setflags(write=False)


@dataclass(frozen=True, slots=True)
class ClimateSample:
    """Independent circulation quantities and latitude-baseline temperature."""

    circulation: CirculationSample
    temperature_c: np.ndarray

    def __post_init__(self) -> None:
        self.temperature_c.setflags(write=False)
