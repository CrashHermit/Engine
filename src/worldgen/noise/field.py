import numpy as np

from src.worldgen.noise.rng import NoiseSource, field_offset
from src.worldgen.types import Float64Array


class FractalField:
    """Multi-octave FBm, ridged, or billow noise over a shared NoiseSource."""

    def __init__(
        self,
        sampler: NoiseSource,
        field_id: int,
        octaves: int = 4,
        lacunarity: float = 2.0,
        gain: float = 0.5,
        kind: str = "fbm",
    ) -> None:
        self._sampler: NoiseSource = sampler
        self._offset: tuple[float, float, float, float] = field_offset(field_id)
        self._octaves: int = octaves
        self._lacunarity: float = lacunarity
        self._gain: float = gain
        self._kind: str = kind

    def sample(self, x: float, y: float, frequency: float) -> float:
        """Return a normalized fractal noise value in roughly [-1, 1]."""
        value: float = 0.0
        amplitude: float = 1.0
        norm: float = 0.0
        freq: float = frequency
        raw: float

        for _ in range(self._octaves):
            raw: float = self._sampler.sample(
                x=x, y=y, frequency=freq, offset=self._offset
            )
            if self._kind == "ridged":
                raw: float = 1.0 - abs(raw)
            elif self._kind == "billow":
                raw: float = abs(raw) * 2.0 - 1.0
            value += raw * amplitude
            norm += amplitude
            amplitude *= self._gain
            freq *= self._lacunarity

        return value / norm if norm > 0.0 else 0.0

    def sample_array(
        self,
        xs: Float64Array,
        ys: Float64Array,
        frequency: float,
    ) -> Float64Array:
        """Sample noise at many ``(x, y)`` pairs; same semantics as :meth:`sample`.

        ``xs`` and ``ys`` must have the same shape; the result has that
        same shape.

        Args:
            xs: X coordinates.
            ys: Y coordinates.
            frequency: Spatial frequency multiplier (passed to
                :meth:`sample`).


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
                self.sample(x=float(x), y=float(y), frequency=frequency)
                for x, y in zip(flat_x, flat_y)
            ),
            dtype=np.float64,
            count=flat_x.size,
        )

        return values.reshape(xs_array.shape)
