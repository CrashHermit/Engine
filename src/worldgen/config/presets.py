from src.worldgen.config.worldgen_config import (
    PlatesConfig,
    SeaLevelConfig,
    WorldgenConfig,
)


def earthlike() -> WorldgenConfig:
    """Balanced continents and oceans."""
    return WorldgenConfig(
        plates=PlatesConfig(continental_fraction=0.45),
        sea_level=SeaLevelConfig(target_land_fraction=0.32),
    )


def archipelago() -> WorldgenConfig:
    """Many small islands; ocean-heavy world."""
    return WorldgenConfig(
        plates=PlatesConfig(n_plates=16, continental_fraction=0.35),
        sea_level=SeaLevelConfig(target_land_fraction=0.20),
    )


def pangaea() -> WorldgenConfig:
    """Single dominant supercontinent."""
    return WorldgenConfig(
        plates=PlatesConfig(n_plates=8, continental_fraction=0.55),
        sea_level=SeaLevelConfig(target_land_fraction=0.45),
    )


PRESETS: dict[str, WorldgenConfig] = {
    "earthlike": earthlike(),
    "archipelago": archipelago(),
    "pangaea": pangaea(),
}
