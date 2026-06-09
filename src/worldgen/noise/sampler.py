from __future__ import annotations

import math

import opensimplex

# Stable domain offsets per logical field ID so multiple independent noise
# fields can share a single opensimplex seed without colliding.  Each field
# gets a large, well-separated shift in 4D space.
_OFFSET_STEP = 97.3
_OFFSET_PHASE = (0.0, 31.7, 67.1, 43.9)


def field_offset(field_id: int) -> tuple[float, float, float, float]:
    """Return a deterministic 4D domain offset for the given field ID."""
    base = field_id * _OFFSET_STEP
    return (
        base + _OFFSET_PHASE[0],
        base + _OFFSET_PHASE[1],
        base + _OFFSET_PHASE[2],
        base + _OFFSET_PHASE[3],
    )


# Named field IDs used throughout the worldgen system.
FIELD_LAYER_BASE: int = 0  # elevation layers: FIELD_LAYER_BASE + layer_index
FIELD_WARP_X: int = 20
FIELD_WARP_Y: int = 21
FIELD_CLIMATE_TEMP_WARP: int = 30
FIELD_CLIMATE_PRECIP: int = 31
FIELD_CLIMATE_PRECIP_WARP: int = 32
FIELD_CLIMATE_WIND_U: int = 33
FIELD_CLIMATE_WIND_V: int = 34
FIELD_ANCHOR_ISLAND: int = 42


class PeriodicSampler:
    """Seamless, isotropic noise sampler using 4D OpenSimplex.

    Maps ``(x, y)`` in ``[0, width) x [0, height)`` to a point on two
    independent unit circles embedded in 4D space so that both axes wrap
    seamlessly and have equal noise speed.  Frequency is applied exactly
    once as the circle radius.
    """

    def __init__(self, width: float, height: float, seed: int) -> None:
        self.width: float = width
        self.height: float = height
        opensimplex.seed(seed)

    def sample(
        self,
        x: float,
        y: float,
        frequency: float,
        offset: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
    ) -> float:
        """Return noise in ``[-1, 1]`` at world position ``(x, y)``.

        Args:
            x: World x coordinate.
            y: World y coordinate.
            frequency: Controls how quickly the noise varies (circle radius).
            offset: Per-field domain offset, use ``field_offset(id)`` to get one.
        """
        ax = 2.0 * math.pi * x / self.width
        ay = 2.0 * math.pi * y / self.height
        r = frequency
        return opensimplex.noise4(
            r * math.cos(ax) + offset[0],
            r * math.sin(ax) + offset[1],
            r * math.cos(ay) + offset[2],
            r * math.sin(ay) + offset[3],
        )
