from dataclasses import replace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.geology.config import CrustConfig, GeologyConfig, PlateConfig
from src.worldgen.generate import generate_world


def test_crust_counts_inheritance_and_independence() -> None:
    config = WorldgenConfig(
        subdivision_frequency=5,
        geology=GeologyConfig(crust=CrustConfig(continental_seeds=3, oceanic_seeds=4)),
    )
    world = generate_world(config)
    crust = world.geology.crust
    assert len(crust.seed_indices) == 7
    assert crust.continental_regions.sum() == 3
    np.testing.assert_array_equal(crust.region_ids[crust.seed_indices], np.arange(7))
    np.testing.assert_array_equal(
        crust.continental_mask,
        crust.continental_regions[crust.region_ids],
    )
    other = generate_world(
        replace(
            config,
            geology=replace(config.geology, plates=PlateConfig(plate_count=9)),
        )
    )
    np.testing.assert_array_equal(crust.region_ids, other.geology.crust.region_ids)
    np.testing.assert_array_equal(
        crust.continental_mask, other.geology.crust.continental_mask
    )


def test_crust_density_is_seeded_and_aggregated_by_crust_region() -> None:
    config = WorldgenConfig(
        seed=2026,
        subdivision_frequency=5,
        geology=GeologyConfig(crust=CrustConfig(continental_seeds=3, oceanic_seeds=4)),
    )
    world = generate_world(config)
    crust = world.geology.crust
    repeat = generate_world(config).geology.crust

    np.testing.assert_array_equal(crust.effective_density, repeat.effective_density)
    np.testing.assert_allclose(
        crust.region_effective_density,
        np.array(
            [
                crust.effective_density[crust.region_ids == region].mean()
                for region in range(len(crust.seed_indices))
            ]
        ),
    )
    assert np.all(crust.effective_density > 0.0)
    assert not crust.effective_density.flags.writeable
    assert not crust.region_effective_density.flags.writeable


def test_density_configuration_does_not_change_geography_or_terrain() -> None:
    config = WorldgenConfig(seed=2026, subdivision_frequency=5)
    changed = replace(
        config,
        geology=replace(
            config.geology,
            crust=replace(
                config.geology.crust,
                density=replace(
                    config.geology.crust.density,
                    continental_base=0.5,
                    oceanic_base=4.0,
                ),
            ),
        ),
    )
    first = generate_world(config)
    second = generate_world(changed)

    np.testing.assert_array_equal(first.geology.plate_ids, second.geology.plate_ids)
    np.testing.assert_array_equal(
        first.geology.crust.region_ids, second.geology.crust.region_ids
    )
    np.testing.assert_allclose(
        first.elevation.coastal_elevation,
        second.elevation.coastal_elevation,
    )
    assert not np.array_equal(
        first.geology.crust.effective_density,
        second.geology.crust.effective_density,
    )
