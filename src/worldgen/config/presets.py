from src.worldgen.config.worldgen_config import (
    MagicConfig,
    PlatesConfig,
    SavageryConfig,
    SeaLevelConfig,
    VulcanismConfig,
    WorldgenConfig,
)

# Land fraction is emergent: sea level sits at the Otsu split between the
# oceanic and continental elevation modes, so whole continental plates surface
# as blobs and the low margins flood (no ribbon-land).  Each preset shapes how
# much land emerges through ``continental_fraction`` (how many plates ride high)
# and a small ``datum_bias`` (sea-level nudge in elevation std-devs; + = less
# land), not a hard quota.


def earthlike() -> WorldgenConfig:
    """Balanced world: a handful of blobby continents in a world ocean."""
    return WorldgenConfig(
        plates=PlatesConfig(n_plates=10, continental_fraction=0.33),
    )


def archipelago() -> WorldgenConfig:
    """Island chains along plate boundaries; ocean-dominated and volcanic."""
    return WorldgenConfig(
        plates=PlatesConfig(
            n_plates=16, continental_fraction=0.18, belt_noise_scale=0.8
        ),
        sea_level=SeaLevelConfig(datum_bias=0.5),  # higher seas -> more ocean
        # Volcanic origin: many hotspots and strong arcs build the islands.
        vulcanism=VulcanismConfig(
            hotspot_count=8, arc_uplift=1.1, ridge_uplift=0.55
        ),
    )


def pangaea() -> WorldgenConfig:
    """One dry supercontinent: few large continental plates that touch."""
    return WorldgenConfig(
        plates=PlatesConfig(
            n_plates=6, continental_fraction=0.6, growth_raggedness=1.0
        ),
        sea_level=SeaLevelConfig(datum_bias=-0.3),  # lower seas -> more land
        # Stable interior: few hotspots, subdued arcs.
        vulcanism=VulcanismConfig(hotspot_count=2, arc_uplift=0.6, ridge_uplift=0.25),
    )


def wildlands() -> WorldgenConfig:
    """Earthlike physique, but savage and leyline-dense."""
    return WorldgenConfig(
        plates=PlatesConfig(n_plates=10, continental_fraction=0.33),
        savagery=SavageryConfig(
            noise_weight=0.35, remoteness_weight=0.40, volcanism_weight=0.25
        ),
        # Denser, branchier veins: stronger rock coupling and a lower vein cutoff.
        magic=MagicConfig(bones_weight=0.8, vein_percentile=85.0),
        vulcanism=VulcanismConfig(hotspot_count=6, arc_uplift=1.0),
    )


PRESETS: dict[str, WorldgenConfig] = {
    "earthlike": earthlike(),
    "archipelago": archipelago(),
    "pangaea": pangaea(),
    "wildlands": wildlands(),
}
