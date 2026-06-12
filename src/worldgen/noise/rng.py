from __future__ import annotations

import math
import zlib

import numpy as np
import opensimplex

from src.worldgen.types import Float64Array

# Each logical field samples a different region of 4D noise space.
_OFFSET_STEP: float = 97.3
_OFFSET_PHASE: tuple[float, float, float, float] = (0.0, 31.7, 67.1, 43.9)

FIELD_ELEVATION: int = 0


def subseed(seed: int, name: str) -> int:
    """Derive a deterministic sub-seed for a named stage or field purpose."""
    return zlib.crc32(f"{seed}:{name}".encode()) & 0x7FFFFFFF


def field_offset(field_id: int) -> tuple[float, float, float, float]:
    """Return a stable 4D offset so fields sharing one NoiseSource stay independent."""
    base: float = field_id * _OFFSET_STEP
    return (
        base + _OFFSET_PHASE[0],
        base + _OFFSET_PHASE[1],
        base + _OFFSET_PHASE[2],
        base + _OFFSET_PHASE[3],
    )


class NoiseSource:
    """Seamless torus noise via a per-world OpenSimplex instance (no global seed)."""

    def __init__(self, seed: int, width: float, height: float) -> None:
        self._width: float = width
        self._height: float = height
        self._noise: opensimplex.OpenSimplex = opensimplex.OpenSimplex(seed)

    def sample(
        self,
        x: float,
        y: float,
        frequency: float,
        offset: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
    ) -> float:
        """Return noise in [-1, 1] at world position (x, y) on the torus."""
        ax: float = 2.0 * math.pi * x / self._width
        ay: float = 2.0 * math.pi * y / self._height
        radius: float = frequency
        return self._noise.noise4(
            x=radius * math.cos(ax) + offset[0],
            y=radius * math.sin(ax) + offset[1],
            z=radius * math.cos(ay) + offset[2],
            w=radius * math.sin(ay) + offset[3],
        )

    def sample_array(
        self,
        xs: Float64Array,
        ys: Float64Array,
        frequency: float,
        offset: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
    ) -> Float64Array:
        """Sample noise at many (x, y) pairs; same semantics as sample()."""
        xs_array: Float64Array = np.asarray(xs, dtype=np.float64)
        ys_array: Float64Array = np.asarray(ys, dtype=np.float64)
        if xs_array.shape != ys_array.shape:
            msg = "xs and ys must have the same shape"
            raise ValueError(msg)

        flat_x: Float64Array = xs_array.ravel()
        flat_y: Float64Array = ys_array.ravel()
        values: Float64Array = np.fromiter(
            (
                self.sample(x=x, y=y, frequency=frequency, offset=offset)
                for x, y in zip(flat_x, flat_y)
            ),
            dtype=np.float64,
            count=flat_x.size,
        )
        return values.reshape(xs_array.shape)
