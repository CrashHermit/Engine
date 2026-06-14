from __future__ import annotations

import math
import zlib

import numpy as np
import opensimplex

from src.worldgen.types import Float64Array

FIELD_ELEVATION: int = 0
FIELD_BOUNDARY_UPLIFT: int = 1
FIELD_UPLIFT_FLOOR: int = 2

def subseed(seed: int, name: str) -> int:
    """Derive a deterministic sub-seed for a named stage or field purpose."""
    return zlib.crc32(f"{seed}:{name}".encode()) & 0x7FFFFFFF


def field_offset(field_id: int) -> tuple[float, float, float, float]:
    """Return a stable 4D offset so fields sharing one NoiseSource stay independent."""
    return tuple(
        float(zlib.crc32(f"field_offset:{field_id}:{axis}".encode()) % 1_000_000) / 1000.0
        for axis in range(4)
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
