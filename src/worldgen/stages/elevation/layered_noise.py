from __future__ import annotations

from src.worldgen.config.worldgen_config import ElevationConfig
from src.worldgen.context import WorldContext
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.sampler import FIELD_LAYER_BASE


class LayeredNoiseProvider:
    """Elevation provider that sums N independent FBm noise bands.

    Each band in ``config.layers`` is a ``NoiseLayerConfig`` with its own
    frequency, weight, octave count, and noise kind.  The default
    configuration uses three bands:

    * Band 0 - continental (large, low-frequency blobs)
    * Band 1 - sub-continental (medium landmasses, sub-seas)
    * Band 2 - island/detail (small islands and coastal texture)

    Adding or removing bands, or changing frequencies and weights, produces
    the full spectrum from a single Pangaea to a speckled archipelago.
    """

    def __init__(self, config: ElevationConfig, ctx: WorldContext) -> None:
        total_weight = sum(layer.weight for layer in config.layers) or 1.0
        self._bands: list[tuple[FractalField, float, float]] = [
            (
                FractalField(
                    ctx.sampler,
                    field_id=FIELD_LAYER_BASE + i,
                    octaves=layer.octaves,
                    kind=layer.kind,
                ),
                layer.frequency,
                layer.weight / total_weight,
            )
            for i, layer in enumerate(config.layers)
        ]

    def elevation_at(self, x: float, y: float) -> float:
        return sum(
            field.sample(x, y, frequency) * weight
            for field, frequency, weight in self._bands
        )
