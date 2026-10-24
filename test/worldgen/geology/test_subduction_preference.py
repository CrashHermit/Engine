import numpy as np

from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.geology.crust_field import CrustField
from src.worldgen.geology.subduction_preference import (
    PolarityConfig,
    SubductionPreferenceField,
    overriding_weights,
)


def _preference(seeds, labels, transition_half_width=0.5):
    partition = VoronoiField3D(np.asarray(seeds, dtype=np.float64))
    regions = RegionInfluenceField(
        partition, RegionInfluenceConfig(transition_half_width)
    )
    crust = CrustField(partition, np.asarray(labels, dtype=np.bool_))
    return SubductionPreferenceField(crust, regions), regions


def test_preference_vectors_retain_seed_and_label_direction():
    seeds = [[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]]
    points = np.array([[0.0, 0.0, 0.0], [0.25, 0.0, 0.0]])
    continental, regions = _preference(seeds, [True, False])
    reversed_material, _ = _preference(seeds, [False, True])

    vectors = continental.sample(points)
    np.testing.assert_allclose(vectors[:, 0], [1.0, 0.828125])
    np.testing.assert_allclose(vectors[:, 1:], 0.0)
    np.testing.assert_allclose(reversed_material.sample(points), -vectors)
    np.testing.assert_array_equal(
        continental.sample_from_regions(points, regions.sample(points)), vectors
    )
    assert not vectors.flags.writeable


def test_preference_field_is_query_set_independent_and_has_typed_empty_output():
    field, _ = _preference([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]], [True, False])
    points = np.random.default_rng(31).uniform(-1.0, 1.0, size=(17, 3))
    full = field.sample(points)
    split = np.concatenate((field.sample(points[:5]), field.sample(points[5:])))
    permutation = np.random.default_rng(32).permutation(len(points))
    reordered = np.empty_like(full)
    reordered[permutation] = field.sample(points[permutation])
    np.testing.assert_array_equal(split, full)
    np.testing.assert_array_equal(reordered, full)

    empty = field.sample(np.empty((0, 3)))
    assert empty.shape == (0, 3)
    assert empty.dtype == np.float64
    assert not empty.flags.writeable


def test_preference_jacobian_uses_vector_sample_contract():
    field, regions = _preference([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]], [True, False])
    points = np.array([[0.1, 0.2, 0.3], [-0.2, 0.1, 0.0]])
    memberships, gradients = regions.sample_with_gradient(points)
    differential = field.sample_with_jacobian(points, memberships, gradients)

    np.testing.assert_array_equal(differential.values, field.sample(points))
    assert differential.jacobians.shape == (2, 3, 3)
    assert not differential.values.flags.writeable
    assert not differential.jacobians.flags.writeable


def test_polarity_weights_separate_seeded_bias_from_preference():
    preference = np.array([-0.2, 0.0, 0.2])
    seeded_sign = np.ones(3)
    seeded = overriding_weights(preference, seeded_sign, directed=False)
    np.testing.assert_array_equal(
        seeded, overriding_weights(-preference, seeded_sign, directed=False)
    )

    directed = overriding_weights(preference, seeded_sign, directed=True)
    assert np.all(np.diff(directed) > 0.0)
    reversed_sides = overriding_weights(
        -preference,
        -seeded_sign,
        directed=True,
    )
    np.testing.assert_allclose(directed + reversed_sides, 1.0, atol=1e-14)

    configured = overriding_weights(
        preference,
        seeded_sign,
        directed=True,
        config=PolarityConfig(preference_scale=0.5, seeded_bias=0.0),
    )
    assert np.all(np.diff(configured) > 0.0)
    assert np.ptp(configured) < np.ptp(directed)
