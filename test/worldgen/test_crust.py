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
