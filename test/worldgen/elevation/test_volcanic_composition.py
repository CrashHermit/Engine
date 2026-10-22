from dataclasses import replace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world_field


def test_volcanic_relief_is_added_once_and_does_not_change_geology():
    config = WorldgenConfig(seed=123)
    enabled = generate_world_field(config)
    disabled = generate_world_field(
        replace(
            config,
            elevation=replace(
                config.elevation,
                volcanism=replace(config.elevation.volcanism, relief_height_percent=0),
            ),
        )
    )
    positions = np.random.default_rng(94).uniform(-1.3, 1.3, (1307, 3))
    rods = enabled.source_elevation.volcanism.hotspots
    source_centers = rods.directions * (rods.lengths * 0.5)[:, None]
    positions = np.concatenate((positions, enabled.warp.inverse(source_centers)))
    a = enabled.sample_world(positions)
    b = disabled.sample_world(positions)
    assert np.any(a.elevation.volcanic_relief > 0)
    np.testing.assert_allclose(
        a.elevation.elevation - b.elevation.elevation,
        a.elevation.volcanic_relief,
        atol=1e-15,
    )
    np.testing.assert_allclose(
        enabled.elevation.sample(positions), a.elevation.elevation, atol=1e-15
    )
    for name in a.geology.__dataclass_fields__:
        np.testing.assert_array_equal(
            getattr(a.geology, name), getattr(b.geology, name)
        )
    np.testing.assert_array_equal(
        a.elevation.volcanic_strength, b.elevation.volcanic_strength
    )
    np.testing.assert_array_equal(
        a.elevation.volcanic_potential, b.elevation.volcanic_potential
    )
    np.testing.assert_array_equal(b.elevation.volcanic_relief, np.zeros(len(positions)))
    np.testing.assert_allclose(
        enabled.volcanic_relief.sample(positions),
        a.elevation.volcanic_relief,
        atol=1e-15,
    )
