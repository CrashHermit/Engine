import numpy as np

from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.region_overlap import RegionOverlapField
from src.worldgen.field.voronoi import VoronoiField3D


def _overlap(seeds: np.ndarray, half_width: float = 0.5) -> RegionOverlapField:
    regions = RegionInfluenceField(
        VoronoiField3D(seeds), RegionInfluenceConfig(half_width)
    )
    return RegionOverlapField(regions)


def test_pair_overlap_uses_compact_membership_product_and_seed_bisector():
    field = _overlap(np.array([[-1.0, 0, 0], [1.0, 0, 0]]))
    positions = np.array(
        [[-0.5, 0, 0], [-0.25, 0, 0], [0, 0, 0], [0.25, 0, 0], [0.5, 0, 0]]
    )

    sample = field.sample(positions)

    np.testing.assert_array_equal(sample.query_indices, [1, 2, 3])
    np.testing.assert_array_equal(sample.region_pairs, [[0, 1], [0, 1], [0, 1]])
    np.testing.assert_allclose(sample.influence, [0.52734375, 1.0, 0.52734375])
    np.testing.assert_allclose(sample.plane_distance, [-0.25, 0.0, 0.25])
    np.testing.assert_allclose(sample.normals, np.tile([1.0, 0, 0], (3, 1)))
    for values in (
        sample.query_indices,
        sample.region_pairs,
        sample.influence,
        sample.plane_distance,
        sample.normals,
    ):
        assert not values.flags.writeable


def test_junction_keeps_each_overlapping_pair_in_lexicographic_order():
    seeds = np.array([[-1.0, 0, 0], [1.0, 0, 0], [0.0, 2.0, 0]])
    sample = _overlap(seeds).sample(np.array([[0.0, 0.75, 0.0]]))

    np.testing.assert_array_equal(sample.query_indices, [0, 0, 0])
    np.testing.assert_array_equal(sample.region_pairs, [[0, 1], [0, 2], [1, 2]])
    np.testing.assert_allclose(sample.influence, np.full(3, 4 / 9))
    np.testing.assert_allclose(np.sum(sample.influence), 4 / 3)


def test_all_pair_overlaps_are_kept_including_nonadjacent_regions():
    seeds = np.array([[-0.05, 0, 0], [0.0, 0, 0], [0.05, 0, 0]])
    sample = _overlap(seeds, 0.12).sample(np.zeros((1, 3)))

    assert [0, 2] in sample.region_pairs.tolist()
    assert np.all(sample.influence > 0.0)
    assert np.all(sample.query_indices == 0)


def test_single_region_and_empty_query_return_typed_immutable_empties():
    single = _overlap(np.array([[0.0, 0.0, 0.0]])).sample(np.zeros((1, 3)))
    empty = _overlap(np.array([[-1.0, 0, 0], [1.0, 0, 0]])).sample(np.empty((0, 3)))

    for sample in (single, empty):
        assert sample.query_indices.shape == (0,)
        assert sample.query_indices.dtype == np.int64
        assert sample.region_pairs.shape == (0, 2)
        assert sample.influence.shape == (0,)
        assert sample.plane_distance.shape == (0,)
        assert sample.normals.shape == (0, 3)
        for values in (
            sample.query_indices,
            sample.region_pairs,
            sample.influence,
            sample.plane_distance,
            sample.normals,
        ):
            assert not values.flags.writeable


def test_repeated_queries_keep_separate_sparse_indices():
    field = _overlap(np.array([[-1.0, 0, 0], [1.0, 0, 0]]))
    sample = field.sample(np.array([[0.0, 0, 0], [0.0, 0, 0]]))

    np.testing.assert_array_equal(sample.query_indices, [0, 1])
    np.testing.assert_allclose(sample.influence, [1.0, 1.0])
