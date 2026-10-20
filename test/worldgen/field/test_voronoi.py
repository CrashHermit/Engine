import numpy as np

from src.worldgen.field.voronoi import VoronoiField3D, sample_voronoi


def test_euclidean_ownership_and_lowest_index_ties():
    seeds = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ]
    )
    positions = np.array(
        [
            [0.25, 0.0, 0.0],
            [0.5, 0.0, 0.0],
            [0.5, 0.5, 0.0],
        ]
    )

    sample = sample_voronoi(positions, seeds)

    np.testing.assert_array_equal(sample.owner_seed_id, [0, 0, 0])


def test_integer_coordinate_arrays_select_nearest_seed():
    positions = np.array([[1, 0, 0], [2, 0, 0]], dtype=np.int64)
    seeds = np.array([[0, 0, 0], [3, 0, 0]], dtype=np.int64)

    sample = sample_voronoi(positions, seeds)

    np.testing.assert_array_equal(sample.owner_seed_id, [0, 1])


def test_bisector_crossing_changes_owner():
    seeds = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    epsilon = 1e-4
    positions = np.array([[0.5 - epsilon, 0.0, 0.0], [0.5 + epsilon, 0.0, 0.0]])

    sample = sample_voronoi(positions, seeds)

    np.testing.assert_array_equal(sample.owner_seed_id, [0, 1])


def test_coincident_seeds_choose_lowest_index_owner():
    seeds = np.zeros((2, 3), dtype=np.float64)

    sample = sample_voronoi(np.array([[0.0, 0.0, 0.0]]), seeds)

    np.testing.assert_array_equal(sample.owner_seed_id, [0])


def test_two_seed_and_empty_query_results_have_typed_read_only_arrays():
    seeds = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
    result = sample_voronoi(np.array([[1.5, 0.0, 0.0]]), seeds)
    np.testing.assert_array_equal(result.owner_seed_id, [1])

    empty = sample_voronoi(np.empty((0, 3)), seeds)
    assert empty.owner_seed_id.shape == (0,)
    assert empty.owner_seed_id.dtype == np.int64
    assert not empty.owner_seed_id.flags.writeable
    assert not result.owner_seed_id.flags.writeable


def test_field_owns_immutable_seed_copy_without_changing_source_array():
    source_seeds = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    original = source_seeds.copy()
    field = VoronoiField3D(source_seeds)
    source_seeds[:] = 50.0

    np.testing.assert_array_equal(field.seeds, original)
    assert field.seeds.dtype == np.float64
    assert not field.seeds.flags.writeable
    sample = field.sample(np.array([[0.2, 0.0, 0.0]]))
    np.testing.assert_array_equal(sample.owner_seed_id, [0])
