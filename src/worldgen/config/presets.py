from __future__ import annotations

from src.worldgen.config.worldgen_config import (
    ElevationConfig,
    NoiseLayerConfig,
    SeaLevelConfig,
    WorldgenConfig,
)


def earthlike() -> WorldgenConfig:
    """Balanced continents and oceans using the layered-noise provider."""
    return WorldgenConfig(
        elevation=ElevationConfig(
            provider="layered_noise",
            layers=[
                NoiseLayerConfig(frequency=0.22, weight=0.50, octaves=4, kind="fbm"),
                NoiseLayerConfig(frequency=0.80, weight=0.35, octaves=4, kind="fbm"),
                NoiseLayerConfig(frequency=2.00, weight=0.15, octaves=3, kind="fbm"),
            ],
            warp_amplitude=0.18,
            redistribution_power=1.35,
        ),
        sea_level=SeaLevelConfig(target_land_fraction=0.32),
    )


def archipelago() -> WorldgenConfig:
    """Many small islands; ocean-heavy world."""
    return WorldgenConfig(
        elevation=ElevationConfig(
            provider="layered_noise",
            layers=[
                NoiseLayerConfig(frequency=0.60, weight=0.40, octaves=3, kind="fbm"),
                NoiseLayerConfig(frequency=2.00, weight=0.35, octaves=3, kind="fbm"),
                NoiseLayerConfig(frequency=5.00, weight=0.25, octaves=2, kind="billow"),
            ],
            warp_amplitude=0.20,
            redistribution_power=1.2,
        ),
        sea_level=SeaLevelConfig(target_land_fraction=0.20),
    )


def pangaea() -> WorldgenConfig:
    """Single dominant supercontinent."""
    return WorldgenConfig(
        elevation=ElevationConfig(
            provider="layered_noise",
            layers=[
                NoiseLayerConfig(frequency=0.10, weight=0.85, octaves=5, kind="fbm"),
                NoiseLayerConfig(frequency=0.60, weight=0.10, octaves=3, kind="fbm"),
                NoiseLayerConfig(frequency=2.50, weight=0.05, octaves=2, kind="fbm"),
            ],
            warp_amplitude=0.10,
            redistribution_power=1.6,
        ),
        sea_level=SeaLevelConfig(target_land_fraction=0.45),
    )


PRESETS: dict[str, WorldgenConfig] = {
    "earthlike": earthlike(),
    "archipelago": archipelago(),
    "pangaea": pangaea(),
}
