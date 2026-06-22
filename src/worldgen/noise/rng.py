import math
import zlib

import numpy as np
import opensimplex

from src.worldgen.types import Float64Array

"""Deterministic noise sources and sub-seeding utilities for the worldgen pipeline.

Every noise field gets its own named sub-seed (via :func:`subseed`) and a stable
4D offset (via :func:`field_offset`) so fields using the same :class:`NoiseSource`
are decorrelated.  No global RNG state.
"""

FIELD_ELEVATION: int = 0
FIELD_BOUNDARY_UPLIFT: int = 1
FIELD_UPLIFT_FLOOR: int = 2
FIELD_EROSION_INIT: int = 3
FIELD_INSOLATION_WOBBLE: int = 4
FIELD_WIND_U: int = 5
FIELD_WIND_V: int = 6


def subseed(seed: int, name: str) -> int:
    """Derive a deterministic sub-seed for a named stage or field purpose.

    Args:
        seed: The world seed (top-level RNG key).
        name: A unique stage or purpose label.

    Returns:
        Deterministic integer in ``[0, 2**31)`` derived from the
        CRC-32 of ``"{seed}:{name}"``.
    """
    return zlib.crc32(f"{seed}:{name}".encode()) & 0x7FFFFFFF


def field_offset(field_id: int) -> tuple[float, float, float, float]:
    """Return a stable 4D offset so fields sharing one NoiseSource stay independent.

    Each field gets its own 4-tuple of floats deterministically derived
    from ``field_id`` via CRC-32.  Offsets are fed into
    :meth:`NoiseSource.sample` so two fields using the same ``NoiseSource``
    produce decorrelated noise.

    Args:
        field_id: Integer constant identifying the field
            (e.g. ``FIELD_ELEVATION``).

    Returns:
        ``(ox, oy, oz, ow)`` — four floats in ``[0, 1000)``.
    """
    return (
        float(zlib.crc32(f"field_offset:{field_id}:0".encode()) % 1_000_000) / 1000.0,
        float(zlib.crc32(f"field_offset:{field_id}:1".encode()) % 1_000_000) / 1000.0,
        float(zlib.crc32(f"field_offset:{field_id}:2".encode()) % 1_000_000) / 1000.0,
        float(zlib.crc32(f"field_offset:{field_id}:3".encode()) % 1_000_000) / 1000.0,
    )


class NoiseSource:
    """Seamless torus noise via a per-world OpenSimplex instance (no global seed)."""

    def __init__(self, seed: int, width: float, height: float) -> None:
        """Wrap an ``OpenSimplex`` instance for one world.

        Args:
            seed: Seed that produces deterministic noise.
            width: Torus width in world units.
            height: Torus height in world units.
        """
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
        """Return noise in ``[-1, 1]`` at a torus position.

        The torus is unwrapped via a 4D mapping (``cos/sin`` of each
        spatial axis) so samples at ``x=0`` and ``x=width`` are equal,
        as required by the periodic mesh.

        Args:
            x: Torus-x coordinate.
            y: Torus-y coordinate.
            frequency: Spatial frequency multiplier.
            offset: 4D offset from :func:`field_offset` for field
                decorrelation.

        Returns:
            Noise value in ``[-1, 1]``.
        """
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
        """Sample noise at many ``(x, y)`` pairs; same semantics as :meth:`sample`.

        ``xs`` and ``ys`` must have the same shape; the result has that
        same shape.

        Args:
            xs: X coordinates.
            ys: Y coordinates.
            frequency: Spatial frequency multiplier (passed to
                :meth:`sample`).
            offset: 4D offset (passed to :meth:`sample`).

        Returns:
            Noise array with the same shape as ``xs`` / ``ys``.
        """
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
