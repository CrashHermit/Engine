from __future__ import annotations

from src.worldgen.noise.sampler import PeriodicSampler, field_offset


class FractalField:
    """Fractal noise field over a ``PeriodicSampler``.

    Generates FBm, ridged, or billow noise by summing ``octaves`` samples at
    geometrically increasing frequencies (controlled by ``lacunarity``) with
    geometrically decreasing amplitudes (controlled by ``gain``).

    Args:
        sampler: Shared ``PeriodicSampler`` for the current world.
        field_id: Unique integer ID selecting the domain offset (use the
            ``FIELD_*`` constants from ``sampler`` module).
        octaves: Number of noise layers to sum.
        lacunarity: Frequency multiplier per octave (default 2.0).
        gain: Amplitude multiplier per octave (default 0.5).
        kind: ``"fbm"`` (default), ``"ridged"``, or ``"billow"``.
    """

    def __init__(
        self,
        sampler: PeriodicSampler,
        field_id: int,
        octaves: int = 4,
        lacunarity: float = 2.0,
        gain: float = 0.5,
        kind: str = "fbm",
    ) -> None:
        self._sampler = sampler
        self._offset = field_offset(field_id)
        self._octaves = octaves
        self._lacunarity = lacunarity
        self._gain = gain
        self._kind = kind

    def sample(self, x: float, y: float, frequency: float) -> float:
        """Return a fractal noise value in roughly ``[-1, 1]``."""
        value = 0.0
        amplitude = 1.0
        norm = 0.0
        freq = frequency

        for _ in range(self._octaves):
            raw = self._sampler.sample(x, y, freq, self._offset)
            if self._kind == "ridged":
                raw = 1.0 - abs(raw)
            elif self._kind == "billow":
                raw = abs(raw) * 2.0 - 1.0
            value += raw * amplitude
            norm += amplitude
            amplitude *= self._gain
            freq *= self._lacunarity

        return value / norm if norm > 0.0 else 0.0


class DomainWarp:
    """Applies domain warping to ``(x, y)`` before sampling another field.

    Two independent fractal fields displace the sample coordinates by
    ``(wx * amplitude, wy * amplitude)``.
    """

    def __init__(
        self,
        sampler: PeriodicSampler,
        field_id_x: int,
        field_id_y: int,
        amplitude: float,
        frequency: float,
        octaves: int = 2,
    ) -> None:
        self._field_x = FractalField(sampler, field_id_x, octaves=octaves)
        self._field_y = FractalField(sampler, field_id_y, octaves=octaves)
        self._amplitude = amplitude
        self._frequency = frequency

    def warp(self, x: float, y: float) -> tuple[float, float]:
        """Return warped ``(x, y)`` coordinates."""
        dx = self._field_x.sample(x, y, self._frequency) * self._amplitude
        dy = self._field_y.sample(x, y, self._frequency) * self._amplitude
        return x + dx, y + dy
