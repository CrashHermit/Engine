from numba import get_num_threads, set_num_threads
import numpy as np

from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.voronoi import VoronoiField3D


def _field(seeds: np.ndarray, half_width: float = 0.5) -> RegionInfluenceField:
    return RegionInfluenceField(
        VoronoiField3D(seeds), RegionInfluenceConfig(half_width)
    )


def test_two_region_memberships_and_overlap_have_compact_smooth_support():
    field = _field(np.array([[-1.0, 0, 0], [1.0, 0, 0]]))
    positions = np.array(
        [[-0.5, 0, 0], [-0.25, 0, 0], [0, 0, 0], [0.25, 0, 0], [0.5, 0, 0]]
    )

    sample = field.sample(positions)

    np.testing.assert_allclose(
        sample.weights,
        [[1, 0], [0.84375, 0.15625], [0.5, 0.5], [0.15625, 0.84375], [0, 1]],
    )
    np.testing.assert_array_equal(sample.voronoi.owner_seed_id, [0, 0, 0, 1, 1])
    assert not sample.weights.flags.writeable
    assert not sample.voronoi.distances_squared.flags.writeable
    assert np.all(sample.weights >= 0.0)
    np.testing.assert_allclose(np.sum(sample.weights, axis=1), 1.0)


def test_two_region_membership_gradients_match_analytic_profile():
    field = _field(np.array([[-1.0, 0, 0], [1.0, 0, 0]]))
    positions = np.column_stack(([-0.5, -0.25, 0.0, 0.25, 0.5], np.zeros((5, 2))))

    sample, gradients = field.sample_with_gradient(positions)

    np.testing.assert_allclose(
        sample.weights,
        field.sample(positions).weights,
    )
    np.testing.assert_allclose(
        gradients[:, 0, 0],
        [0.0, -1.125, -1.5, -1.125, 0.0],
    )
    np.testing.assert_allclose(
        gradients[:, 1, 0],
        [0.0, 1.125, 1.5, 1.125, 0.0],
    )
    np.testing.assert_array_equal(gradients[:, :, 1:], 0.0)
    np.testing.assert_allclose(np.sum(gradients, axis=1), 0.0)
    assert not sample.weights.flags.writeable
    assert not gradients.flags.writeable


def test_membership_gradients_match_finite_differences_and_query_layouts():
    rng = np.random.default_rng(90210)
    seeds = rng.uniform(-1.0, 1.0, (8, 3))
    positions = rng.uniform(-1.0, 1.0, (17, 3))
    seeds_before = seeds.copy()
    positions.setflags(write=False)
    positions_before = positions.copy()
    field = _field(seeds, 0.5)

    sample, gradients = field.sample_with_gradient(positions)

    step = 1e-6
    numerical_gradients = np.empty_like(gradients)
    for axis in range(3):
        positive = positions.copy()
        negative = positions.copy()
        positive[:, axis] += step
        negative[:, axis] -= step
        numerical_gradients[:, :, axis] = (
            field.sample(positive).weights - field.sample(negative).weights
        ) / (2.0 * step)
    np.testing.assert_allclose(
        gradients,
        numerical_gradients,
        rtol=1e-5,
        atol=1e-8,
    )

    split_samples = [
        field.sample_with_gradient(positions[:7]),
        field.sample_with_gradient(positions[7:]),
    ]
    np.testing.assert_array_equal(
        np.concatenate([part.weights for part, _ in split_samples]),
        sample.weights,
    )
    np.testing.assert_array_equal(
        np.concatenate([part for _, part in split_samples]),
        gradients,
    )

    permutation = np.arange(len(positions))[::-1]
    reordered, reordered_gradients = field.sample_with_gradient(positions[permutation])
    np.testing.assert_array_equal(reordered.weights, sample.weights[permutation])
    np.testing.assert_array_equal(reordered_gradients, gradients[permutation])

    strided_base = np.empty((34, 3), dtype=np.float64)
    strided_base[::2] = positions
    strided_base[1::2] = positions
    strided_base.setflags(write=False)
    strided_sample, strided_gradients = field.sample_with_gradient(strided_base[::2])
    np.testing.assert_array_equal(strided_sample.weights, sample.weights)
    np.testing.assert_array_equal(strided_gradients, gradients)
    np.testing.assert_array_equal(seeds, seeds_before)
    np.testing.assert_array_equal(positions, positions_before)
    assert not sample.weights.flags.writeable
    assert not gradients.flags.writeable
    assert not strided_sample.weights.flags.writeable
    assert not strided_gradients.flags.writeable


def test_transition_width_is_source_space_distance_not_cell_fraction():
    wide = _field(np.array([[-1.0, 0, 0], [1.0, 0, 0]]))
    narrow = _field(np.array([[-0.01, 0, 0], [0.01, 0, 0]]))
    positions = np.array([[0.0, 0, 0], [0.25, 0, 0]])

    wide_weights = wide.sample(positions).weights
    narrow_weights = narrow.sample(positions).weights

    np.testing.assert_allclose(wide_weights, narrow_weights)


def test_three_region_junction_blends_all_competitors():
    field = _field(np.array([[-1.0, 0, 0], [1.0, 0, 0], [0.0, 2.0, 0]]))

    sample = field.sample(np.array([[0.0, 0.75, 0.0]]))

    np.testing.assert_allclose(sample.weights, [[1 / 3, 1 / 3, 1 / 3]])


def test_square_junction_keeps_all_six_seed_pairs_influence():
    field = _field(
        np.array([[-1.0, -1.0, 0], [-1.0, 1.0, 0], [1.0, -1.0, 0], [1.0, 1.0, 0]])
    )

    sample = field.sample(np.zeros((1, 3)))

    np.testing.assert_allclose(sample.weights, np.full((1, 4), 0.25))
    np.testing.assert_array_equal(
        field.region_pairs,
        [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]],
    )


def test_narrow_middle_region_does_not_suppress_outer_pair_blend():
    field = _field(np.array([[-0.05, 0, 0], [0.0, 0, 0], [0.05, 0, 0]]), 0.12)

    sample = field.sample(np.zeros((1, 3)))

    assert np.all(sample.weights > 0.0)
    assert np.isclose(np.sum(sample.weights), 1.0)


def test_single_region_and_empty_queries_return_immutable_typed_results():
    field = _field(np.array([[0.2, -0.1, 0.3]]))
    sample, gradients = field.sample_with_gradient(np.array([[0.0, 0.0, 0.0]]))
    empty, empty_gradients = field.sample_with_gradient(np.empty((0, 3)))

    np.testing.assert_array_equal(sample.weights, [[1.0]])
    np.testing.assert_array_equal(gradients, np.zeros((1, 1, 3)))
    assert field.region_pairs.shape == (0, 2)
    assert field.pair_normals.shape == (0, 3)
    assert empty.weights.shape == (0, 1)
    assert empty.weights.dtype == np.float64
    assert empty.voronoi.distances_squared.shape == (0, 1)
    assert empty_gradients.shape == (0, 1, 3)
    assert empty_gradients.dtype == np.float64
    assert not sample.weights.flags.writeable
    assert not gradients.flags.writeable
    assert not empty.weights.flags.writeable
    assert not empty_gradients.flags.writeable


def test_seed_permutation_and_query_splitting_preserve_memberships():
    seeds = np.array([[-1.0, 0, 0], [1.0, 0, 0], [0.0, 2.0, 0]])
    permutation = np.array([2, 0, 1])
    positions = np.array([[0.0, 0.75, 0.0], [0.2, 0.4, 0.0], [-0.3, 0.2, 0.0]])
    original = _field(seeds).sample(positions)
    reordered = _field(seeds[permutation]).sample(positions)

    np.testing.assert_allclose(reordered.weights, original.weights[:, permutation])
    np.testing.assert_array_equal(
        _field(seeds).sample(positions[[0, 2]]).weights, original.weights[[0, 2]]
    )
    duplicated = _field(seeds).sample(positions[[1, 1]])
    np.testing.assert_array_equal(duplicated.weights[0], duplicated.weights[1])


def test_memberships_have_zero_endpoint_slope_and_continuous_junction_derivatives():
    field = _field(np.array([[-1.0, 0, 0], [1.0, 0, 0]]))
    epsilon = 1e-6
    endpoint = field.sample(
        np.array([[0.5 - epsilon, 0, 0], [0.5, 0, 0], [0.5 + epsilon, 0, 0]])
    ).weights

    left_slope = (endpoint[1, 0] - endpoint[0, 0]) / epsilon
    right_slope = (endpoint[2, 0] - endpoint[1, 0]) / epsilon
    assert abs(left_slope) < 5e-6
    assert abs(right_slope) < 5e-6

    junction = _field(np.array([[-1.0, 0, 0], [1.0, 0, 0], [0.0, 2.0, 0]]))
    center = np.array([[0.0, 0.75, 0.0]])
    offsets = np.array([[-epsilon, 0, 0], [0.0, 0, 0], [epsilon, 0, 0]]) + center
    weights = junction.sample(offsets).weights
    left_derivative = (weights[1] - weights[0]) / epsilon
    right_derivative = (weights[2] - weights[1]) / epsilon
    np.testing.assert_allclose(left_derivative, right_derivative, atol=2e-4)


def test_parallel_memberships_and_gradients_match_independent_query_chunks():
    rng = np.random.default_rng(7310)
    field = _field(rng.uniform(-1.0, 1.0, (40, 3)), 0.3)
    positions = rng.uniform(-1.5, 1.5, (514, 3))[::2]
    positions.setflags(write=False)
    before = positions.copy()
    chunks = [
        field.sample_with_gradient(positions[start : start + 17])
        for start in range(0, len(positions), 17)
    ]
    expected_weights = np.concatenate([sample.weights for sample, _ in chunks])
    expected_gradients = np.concatenate([gradient for _, gradient in chunks])

    original_threads = get_num_threads()
    try:
        for thread_count in (1, min(4, original_threads)):
            set_num_threads(thread_count)
            for _ in range(2):
                values = field.sample(positions)
                sample, gradients = field.sample_with_gradient(positions)
                np.testing.assert_array_equal(values.weights, expected_weights)
                np.testing.assert_array_equal(sample.weights, expected_weights)
                np.testing.assert_array_equal(gradients, expected_gradients)
                assert not values.weights.flags.writeable
                assert not sample.weights.flags.writeable
                assert not gradients.flags.writeable
    finally:
        set_num_threads(original_threads)
    np.testing.assert_array_equal(positions, before)
