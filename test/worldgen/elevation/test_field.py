import numpy as np
from dataclasses import replace

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world_field


def test_source_elevation_is_batch_and_order_independent():
    field = generate_world_field(WorldgenConfig(seed=2026)).source_elevation
    points = np.random.default_rng(13).normal(size=(21, 3))
    full = field.sample_source(points)
    order = np.array([12, 4, 0, 20, 7])
    subset = field.sample_source(points[order])

    for name in full.__dataclass_fields__:
        np.testing.assert_array_equal(getattr(subset, name), getattr(full, name)[order])
        assert getattr(full, name).dtype == np.float64
        assert not getattr(full, name).flags.writeable
    np.testing.assert_array_equal(field.sample_total_source(points), full.total)


def test_ridge_detail_changes_collision_without_changing_other_responses():
    config = WorldgenConfig(seed=123)
    plain_config = replace(
        config,
        elevation=replace(
            config.elevation,
            ridge_detail=replace(config.elevation.ridge_detail, blend=0.0),
        ),
    )
    detailed = generate_world_field(config)
    plain = generate_world_field(plain_config)
    points = np.random.default_rng(2026).uniform(-1.4, 1.4, size=(1307, 3))
    a = detailed.sample_world(points)
    b = plain.sample_world(points)
    assert np.any(a.elevation.convergent_relief != b.elevation.convergent_relief)
    for name in (
        "coastal_elevation",
        "divergent_relief",
        "transform_relief",
        "shear_relief",
        "terrain_variation",
    ):
        np.testing.assert_array_equal(
            getattr(a.elevation, name), getattr(b.elevation, name)
        )
    for name in ("convergence", "divergence", "shear"):
        np.testing.assert_array_equal(
            getattr(a.geology, name), getattr(b.geology, name)
        )
    np.testing.assert_allclose(
        detailed.convergent_relief.sample(points),
        a.elevation.convergent_relief,
        atol=1e-15,
    )


def test_source_elevation_empty_queries_are_typed_readonly():
    field = generate_world_field(WorldgenConfig(seed=17)).source_elevation
    empty = field.sample_source(np.empty((0, 3), dtype=np.float64))
    total = field.sample_total_source(np.empty((0, 3), dtype=np.float64))

    for name in empty.__dataclass_fields__:
        values = getattr(empty, name)
        assert values.shape == (0,)
        assert values.dtype == np.float64
        assert not values.flags.writeable
    assert total.shape == (0,)
    assert total.dtype == np.float64
    assert not total.flags.writeable
