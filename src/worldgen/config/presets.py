from __future__ import annotations

from src.worldgen.config.worldgen_config import (
    AnchorConfig,
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
                NoiseLayerConfig(frequency=0.20, weight=0.65, octaves=4, kind="fbm"),
                NoiseLayerConfig(frequency=0.75, weight=0.25, octaves=3, kind="fbm"),
                NoiseLayerConfig(frequency=2.50, weight=0.10, octaves=2, kind="fbm"),
            ],
            warp_amplitude=0.15,
            redistribution_power=1.4,
        ),
        sea_level=SeaLevelConfig(target_land_fraction=0.30),
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


def directed_continents(num: int = 3) -> WorldgenConfig:
    """Directed placement of ``num`` continents via the anchor provider."""
    return WorldgenConfig(
        elevation=ElevationConfig(provider="anchors"),
        sea_level=SeaLevelConfig(target_land_fraction=0.30),
        anchor=AnchorConfig(
            num_continents=num,
            continent_radius=0.30,
            min_continent_spacing=0.40,
            island_count=6,
            island_radius=0.08,
        ),
    )


PRESETS: dict[str, WorldgenConfig] = {
    "earthlike": earthlike(),
    "archipelago": archipelago(),
    "pangaea": pangaea(),
    "directed_continents": directed_continents(),
}
