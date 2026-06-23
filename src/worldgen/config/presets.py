from src.worldgen.config.worldgen_config import (
    LeylineConfig,
    PlatesConfig,
    SavageryConfig,
    SeaLevelConfig,
    WorldgenConfig,
)

# House rule for blobby continents: keep target_land_fraction >= the realized
# continental area (≈ continental_fraction). Sea level then falls in the gap
# between the oceanic and continental elevation modes, so whole continental
# plates surface as landmasses. When target_land_fraction sits *below* the
# continental area, sea level cuts through the continental band and drowns
# everything but the high spines — that is what produced thin ribbon-land.


def earthlike() -> WorldgenConfig:
    """Balanced world: a handful of blobby continents in a world ocean."""
    return WorldgenConfig(
        plates=PlatesConfig(n_plates=10, continental_fraction=0.33),
        sea_level=SeaLevelConfig(target_land_fraction=0.38),
    )


def archipelago() -> WorldgenConfig:
    """Island chains along plate boundaries; ocean-dominated."""
    return WorldgenConfig(
        plates=PlatesConfig(
            n_plates=16, continental_fraction=0.18, belt_noise_scale=0.8
        ),
        sea_level=SeaLevelConfig(target_land_fraction=0.24),
    )


def pangaea() -> WorldgenConfig:
    """One dry supercontinent: few large continental plates that touch."""
    return WorldgenConfig(
        plates=PlatesConfig(
            n_plates=6, continental_fraction=0.6, growth_raggedness=1.0
        ),
        sea_level=SeaLevelConfig(target_land_fraction=0.64),
    )


def wildlands() -> WorldgenConfig:
    """Earthlike physique, but savage, leyline-dense, and corruption-leaning."""
    return WorldgenConfig(
        plates=PlatesConfig(n_plates=10, continental_fraction=0.33),
        sea_level=SeaLevelConfig(target_land_fraction=0.38),
        savagery=SavageryConfig(noise_weight=0.35, remoteness_weight=0.40),
        leyline=LeylineConfig(count=30, purity=3.0),
    )


PRESETS: dict[str, WorldgenConfig] = {
    "earthlike": earthlike(),
    "archipelago": archipelago(),
    "pangaea": pangaea(),
    "wildlands": wildlands(),
}
