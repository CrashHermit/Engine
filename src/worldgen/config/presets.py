from src.worldgen.config.worldgen_config import (
    LeylineConfig,
    PlatesConfig,
    SavageryConfig,
    SeaLevelConfig,
    WorldgenConfig,
)


def earthlike() -> WorldgenConfig:
    """Balanced continents and oceans — the default physique."""
    return WorldgenConfig(
        plates=PlatesConfig(n_plates=10, continental_fraction=0.45),
        sea_level=SeaLevelConfig(target_land_fraction=0.32),
    )


def archipelago() -> WorldgenConfig:
    """Many small islands strung along plate boundaries; ocean-heavy world."""
    return WorldgenConfig(
        plates=PlatesConfig(
            n_plates=16, continental_fraction=0.35, belt_noise_scale=0.8
        ),
        sea_level=SeaLevelConfig(target_land_fraction=0.20),
    )


def pangaea() -> WorldgenConfig:
    """Few, touching continental plates → one supercontinent with a dry interior."""
    return WorldgenConfig(
        plates=PlatesConfig(
            n_plates=6, continental_fraction=0.7, growth_raggedness=1.0
        ),
        sea_level=SeaLevelConfig(target_land_fraction=0.42),
    )


def wildlands() -> WorldgenConfig:
    """Demonstrate the fantasy knobs: savage, leyline-dense, corruption-leaning."""
    return WorldgenConfig(
        plates=PlatesConfig(n_plates=10, continental_fraction=0.45),
        sea_level=SeaLevelConfig(target_land_fraction=0.32),
        savagery=SavageryConfig(noise_weight=0.35, remoteness_weight=0.40),
        leyline=LeylineConfig(count=30, purity=3.0),
    )


PRESETS: dict[str, WorldgenConfig] = {
    "earthlike": earthlike(),
    "archipelago": archipelago(),
    "pangaea": pangaea(),
    "wildlands": wildlands(),
}
