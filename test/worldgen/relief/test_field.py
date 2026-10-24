import numpy as np
from dataclasses import replace
from scipy.spatial import Voronoi

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world_field
from src.worldgen.relief.field import SourceReliefField


def test_source_relief_is_batch_and_order_independent():
    field = generate_world_field(WorldgenConfig(seed=2026)).source_relief
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
        relief=replace(
            config.relief,
            ridge_detail=replace(config.relief.ridge_detail, blend=0.0),
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


def test_source_relief_empty_queries_are_typed_readonly():
    field = generate_world_field(WorldgenConfig(seed=17)).source_relief
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


def test_shared_relief_inputs_preserve_components_and_gradients_at_junctions():
    world = generate_world_field(WorldgenConfig(seed=2026))
    geology = world.geology
    original = world.source_relief
    field = SourceReliefField(
        sample_relief_inputs=geology.sample_relief_inputs,
        sample_relief_inputs_with_gradient=geology.sample_relief_inputs_with_gradient,
        coastal=original.coastal,
        sampler=original.sampler,
        tectonic=original.tectonic,
        convergent=original.convergent,
        divergent=original.divergent,
        transform=original.transform,
        shear=original.shear,
    )
    # A genuine four-region junction, not a midpoint assumed to be a boundary.
    vertices = Voronoi(geology.regions.voronoi.seeds).vertices
    junction = vertices[np.argmin(np.linalg.norm(vertices, axis=1))]
    candidates = np.random.default_rng(37).uniform(-1.5, 1.5, (128, 3))
    candidate_inputs = geology.sample_relief_inputs(candidates)
    counts = np.bincount(candidate_inputs.query_indices, minlength=len(candidates))
    interior = candidates[np.flatnonzero(counts == 0)[0]]
    points = np.vstack([np.zeros(3), [2.1, -1.8, 0.7], interior, junction, candidates])
    backing = np.repeat(points, 2, axis=0)
    backing.setflags(write=False)
    points = backing[::2]
    full = original.sample_source(points)
    full_gradient = original.sample_source_with_gradient(points)
    assert len(geology.sample_relief_inputs(points[2:3]).query_indices) == 0
    assert len(geology.sample_relief_inputs(points[3:4]).query_indices) >= 3

    for rows in (
        np.arange(len(points)),
        np.array([3, 0, 2, 1, 3]),
        np.arange(0, 41),
        np.arange(41, len(points)),
        np.empty(0, dtype=np.int64),
    ):
        query = points if len(rows) == len(points) else points[rows]
        values = field.sample_source(
            query, relief_inputs=geology.sample_relief_inputs(query)
        )
        gradients = field.sample_source_with_gradient(
            query, relief_inputs=geology.sample_relief_inputs_with_gradient(query)
        )
        direct_values = field.sample_source(query)
        direct_gradients = field.sample_source_with_gradient(query)
        for name in full.__dataclass_fields__:
            actual = getattr(values, name)
            derivative = getattr(gradients, name)
            np.testing.assert_array_equal(actual, getattr(full, name)[rows])
            np.testing.assert_array_equal(actual, getattr(direct_values, name))
            np.testing.assert_array_equal(
                derivative.values, getattr(full_gradient, name).values[rows]
            )
            np.testing.assert_allclose(
                derivative.gradients,
                getattr(full_gradient, name).gradients[rows],
                rtol=1e-12,
                atol=1e-12,
            )
            np.testing.assert_allclose(
                derivative.gradients,
                getattr(direct_gradients, name).gradients,
                rtol=1e-12,
                atol=1e-12,
            )
            assert actual.shape == (len(query),)
            assert derivative.gradients.shape == (len(query), 3)
            assert not actual.flags.writeable
            assert not derivative.values.flags.writeable
            assert not derivative.gradients.flags.writeable
