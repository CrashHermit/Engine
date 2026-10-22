import numpy as np

from src.worldgen.field.boundary_vector import BoundaryVectorField
from src.worldgen.field.motion import RegionRotationField
from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.region_overlap import RegionOverlapField
from src.worldgen.field.voronoi import VoronoiField3D


def _boundary_vectors(
    seeds: np.ndarray,
    angular_velocity: np.ndarray,
    *,
    width: float,
) -> BoundaryVectorField:
    partition = VoronoiField3D(seeds)
    influence = RegionInfluenceField(
        partition, RegionInfluenceConfig(transition_half_width=width)
    )
    overlap = RegionOverlapField(influence)
    motion = RegionRotationField(partition, angular_velocity)
    return BoundaryVectorField(overlap, motion.sample_regions)


def _assert_read_only(sample) -> None:
    for array in (
        sample.query_indices,
        sample.region_pairs,
        sample.influence,
        sample.vectors,
        sample.plane_distance,
        sample.normals,
    ):
        assert not array.flags.writeable


def test_overlap_pairs_evaluate_unique_region_vectors() -> None:
    field = _boundary_vectors(
        np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [10.0, 0.0, 0.0]]),
        np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 2.0], [0.0, 0.0, 1000.0]]),
        width=0.5,
    )

    sample = field.sample(np.array([[0.0, 1.0, 0.0], [0.25, 1.0, 0.0]]))

    # A pair without an actual Voronoi face is still emitted when both labels overlap.
    nonadjacent = _boundary_vectors(
        np.array([[-0.05, 0.0, 0.0], [0.0, 0.0, 0.0], [0.05, 0.0, 0.0]]),
        np.eye(3),
        width=0.12,
    ).sample(np.array([[0.0, 0.0, 0.0]]))
    assert np.any(np.all(nonadjacent.region_pairs == [0, 2], axis=1))
    assert np.all(nonadjacent.influence > 0.0)
    pair_01 = np.all(sample.region_pairs == [0, 1], axis=1)
    np.testing.assert_array_equal(sample.query_indices[pair_01], [0, 1])
    np.testing.assert_allclose(sample.influence[pair_01], [1.0, 0.52734375])
    np.testing.assert_allclose(sample.plane_distance[pair_01], [0.0, 0.25])
    np.testing.assert_allclose(sample.normals[pair_01], [[1, 0, 0], [1, 0, 0]])
    _assert_read_only(sample)


def test_triple_junction_keeps_all_pairs_and_vector_slots() -> None:
    field = _boundary_vectors(
        np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0]]),
        np.eye(3),
        width=0.5,
    )

    sample = field.sample(np.array([[0.0, 0.75, 0.0]]))

    np.testing.assert_array_equal(sample.query_indices, [0, 0, 0])
    np.testing.assert_array_equal(sample.region_pairs, [[0, 1], [0, 2], [1, 2]])
    np.testing.assert_allclose(sample.influence, [4 / 9, 4 / 9, 4 / 9])
    np.testing.assert_allclose(
        sample.vectors,
        [
            [[0.0, 0.0, 0.75], [0.0, 0.0, 0.0]],
            [[0.0, 0.0, 0.75], [-0.75, 0.0, 0.0]],
            [[0.0, 0.0, 0.0], [-0.75, 0.0, 0.0]],
        ],
    )


def test_composition_accepts_nonrotational_region_vector_sampler() -> None:
    partition = VoronoiField3D(np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]))
    regional = RegionInfluenceField(
        partition, RegionInfluenceConfig(transition_half_width=0.5)
    )
    overlap = RegionOverlapField(regional)

    def linear_region_vectors(positions: np.ndarray, region_ids: np.ndarray):
        return np.column_stack(
            (
                positions[:, 0] + region_ids,
                2.0 * positions[:, 1],
                positions[:, 2] - region_ids,
            )
        )

    field = BoundaryVectorField(overlap, linear_region_vectors)
    sample = field.sample(np.array([[0.0, 1.0, 0.0]]))

    np.testing.assert_array_equal(sample.region_pairs, [[0, 1]])
    np.testing.assert_allclose(sample.vectors, [[[0.0, 2.0, 0.0], [1.0, 2.0, -1.0]]])


def test_empty_and_single_region_samples_are_typed_immutable_records() -> None:
    positions = np.empty((0, 3))
    for seeds, queries in (
        (np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]), positions),
        (np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]), np.array([[20.0, 20.0, 20.0]])),
        (np.array([[0.0, 0.0, 0.0]]), positions),
        (np.array([[0.0, 0.0, 0.0]]), np.array([[20.0, 20.0, 20.0]])),
    ):
        field = _boundary_vectors(seeds, np.zeros((len(seeds), 3)), width=0.5)
        sample = field.sample(queries)
        assert sample.query_indices.shape == (0,)
        assert sample.query_indices.dtype == np.int64
        assert sample.region_pairs.shape == (0, 2)
        assert sample.region_pairs.dtype == np.int64
        assert sample.influence.shape == sample.plane_distance.shape == (0,)
        assert sample.normals.shape == (0, 3)
        assert sample.vectors.shape == (0, 2, 3)
        _assert_read_only(sample)


def test_boundary_vector_sampling_is_batch_and_order_independent() -> None:
    field = _boundary_vectors(
        np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0]]),
        np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 2.0], [0.0, 0.0, 3.0]]),
        width=0.4,
    )
    points = np.random.default_rng(8).uniform(-1.0, 1.0, size=(1307, 3))
    full = field.sample(points)
    parts = [
        field.sample(points[start : start + 173])
        for start in range(0, len(points), 173)
    ]
    split_indices = np.concatenate(
        [
            sample.query_indices + start
            for start, sample in zip(range(0, len(points), 173), parts)
        ]
    )
    for name in ("region_pairs", "influence", "vectors", "plane_distance", "normals"):
        np.testing.assert_array_equal(
            np.concatenate([getattr(sample, name) for sample in parts]),
            getattr(full, name),
        )
    np.testing.assert_array_equal(split_indices, full.query_indices)
    order = np.random.default_rng(19).permutation(len(points))
    reordered = field.sample(points[order])
    original_indices = order[reordered.query_indices]
    stable_order = np.argsort(original_indices, kind="stable")
    np.testing.assert_array_equal(original_indices[stable_order], full.query_indices)
    for name in ("region_pairs", "influence", "vectors", "plane_distance", "normals"):
        np.testing.assert_array_equal(
            getattr(reordered, name)[stable_order], getattr(full, name)
        )


def test_duplicate_positions_remain_distinct_and_overlap_is_pointwise() -> None:
    field = _boundary_vectors(
        np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 2.0]]),
        width=0.5,
    )
    points = np.array([[0.0, 1.0, 0.0], [0.0, 1.0, 0.0]])
    sample = field.sample(points)
    np.testing.assert_array_equal(sample.query_indices, [0, 1])
    np.testing.assert_array_equal(sample.region_pairs, [[0, 1], [0, 1]])
    np.testing.assert_array_equal(sample.influence, [1.0, 1.0])
    np.testing.assert_array_equal(sample.plane_distance, [0.0, 0.0])
    np.testing.assert_array_equal(sample.vectors[0], sample.vectors[1])

    points = np.array([[0.125, 0.37, -0.22], [0.0, 2.137, -3.41]])
    sample = field.sample(points)
    np.testing.assert_array_equal(sample.query_indices, [0, 1])
    np.testing.assert_allclose(sample.influence, [0.86517333984375, 1.0])
    np.testing.assert_array_equal(
        field.sample(points[1:2]).vectors, sample.vectors[1:2]
    )
