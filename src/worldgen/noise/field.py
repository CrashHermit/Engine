from src.worldgen.noise.rng import NoiseSource, field_offset


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
