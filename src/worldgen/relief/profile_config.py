"""Configuration shared by tectonic relief profiles."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReliefProfileConfig:
    """Tectonic profile width and relief height as percentages of radius."""

    width_percent: float = 12.0
    height_percent: float = 0.0392

    @property
    def width_fraction(self) -> float:
        """Return source-space width as a fraction of unit-sphere radius."""
        return self.width_percent / 100.0

    @property
    def height_fraction(self) -> float:
        """Return relief height as a fraction of unit-sphere radius."""
        return self.height_percent / 100.0
