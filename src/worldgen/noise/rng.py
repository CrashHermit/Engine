from __future__ import annotations

import math
import zlib

import numpy as np
import opensimplex

from src.worldgen.types import Float64Array

# Stable domain offsets per logical field ID so multiple independent noise
# fields can share one NoiseSource without colliding in 4D space.
_OFFSET_STEP = 97.3
_OFFSET_PHASE = (0.0, 31.7, 67.1, 43.9)


def subseed(seed: int, name: str) -> int:
    """Derive a deterministic sub-seed for a named stage or field purpose."""
    return zlib.crc32(f"{seed}:{name}".encode()) & 0x7FFFFFFF


def field_offset(field_id: int) -> tuple[float, float, float, float]:
    """Return a deterministic 4D domain offset for the given field ID."""
    base = field_id * _OFFSET_STEP
    return (
        base + _OFFSET_PHASE[0],
        base + _OFFSET_PHASE[1],
        base + _OFFSET_PHASE[2],
        base + _OFFSET_PHASE[3],
    )


class NoiseSource:
    """Instance-based seamless torus noise; replaces global opensimplex.seed()."""

    def __init__(self, seed: int, width: float, height: float) -> None:
        self._width = width
        self._height = height
        self._noise = opensimplex.OpenSimplex(seed)

    def sample(
        self,
        x: float,
        y: float,
        frequency: float,
        offset: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
    ) -> float:
        """Return noise in [-1, 1] at world position (x, y) on the torus."""
        ax = 2.0 * math.pi * x / self._width
        ay = 2.0 * math.pi * y / self._height
        radius = frequency
        return self._noise.noise4(
            radius * math.cos(ax) + offset[0],
            radius * math.sin(ax) + offset[1],
            radius * math.cos(ay) + offset[2],
            radius * math.sin(ay) + offset[3],
        )

    def sample_array(
        self,
        xs: Float64Array,
        ys: Float64Array,
        frequency: float,
        offset: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
    ) -> Float64Array:
        """Sample noise at many (x, y) pairs; same semantics as sample()."""
        xs_array = np.asarray(xs, dtype=np.float64)
        ys_array = np.asarray(ys, dtype=np.float64)
        if xs_array.shape != ys_array.shape:
            msg = "xs and ys must have the same shape"
            raise ValueError(msg)

        flat_x = xs_array.ravel()
        flat_y = ys_array.ravel()
        values = np.fromiter(
            (self.sample(float(x), float(y), frequency, offset) for x, y in zip(flat_x, flat_y)),
            dtype=np.float64,
            count=flat_x.size,
        )
        return values.reshape(xs_array.shape)
