import numpy as np

from src.worldgen.field.boundary import (
    BoundaryInfluenceConfig,
    build_voronoi_boundary_field,
)
from src.worldgen.field.boundary_vector import BoundaryVectorField
from src.worldgen.field.motion import RegionRotationField
from src.worldgen.field.regions import WarpedVoronoiField
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField


def _identity_warp() -> ShearWarpField:
    return ShearWarpField(
        ShearWarpConfig(iterations=0),
        lambda plane, iteration, axis, frequency: np.zeros(len(plane)),
    )


def _regions(seeds: np.ndarray, warp: ShearWarpField | None = None):
    return WarpedVoronoiField(
        warp=warp or _identity_warp(), voronoi=VoronoiField3D(seeds)
    )


def _boundary_vectors(
    seeds: np.ndarray,
    angular_velocity: np.ndarray,
    *,
    width: float,
    warp: ShearWarpField | None = None,
) -> BoundaryVectorField:
    regions = _regions(seeds, warp)
    motion = RegionRotationField(regions, angular_velocity)
    boundary = build_voronoi_boundary_field(
        regions, BoundaryInfluenceConfig(width=width)
    )
    return BoundaryVectorField(boundary, motion.sample_regions)


def _assert_read_only(sample) -> None:
    for array in (
        sample.query_indices,
        sample.region_pairs,
        sample.influence,
        sample.vectors,
    ):
        assert not array.flags.writeable


def test_only_active_adjacent_regions_are_evaluated_at_each_query() -> None:
    field = _boundary_vectors(
        np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [10.0, 0.0, 0.0]]),
        np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 2.0], [0.0, 0.0, 1000.0]]),
        width=0.5,
    )

    sample = field.sample(
        np.array([[0.0, 1.0, 0.0], [0.25, 1.0, 0.0], [0.5, 1.0, 0.0], [1.0, 1.0, 0.0]])
    )

    np.testing.assert_array_equal(sample.query_indices, [0, 1])
    np.testing.assert_array_equal(sample.region_pairs, [[0, 1], [0, 1]])
    np.testing.assert_allclose(sample.influence, [1.0, 0.5])
    np.testing.assert_allclose(
        sample.vectors,
        [[[-1.0, 0.0, 0.0], [-2.0, 0.0, 0.0]], [[-1.0, 0.25, 0.0], [-2.0, 0.5, 0.0]]],
    )
    _assert_read_only(sample)


def test_triple_junction_keeps_all_pair_interactions_and_vector_slots() -> None:
    field = _boundary_vectors(
        np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0]]),
        np.eye(3),
        width=0.25,
    )

    sample = field.sample(np.array([[0.0, 0.75, 0.0]]))

    np.testing.assert_array_equal(sample.query_indices, [0, 0, 0])
    np.testing.assert_array_equal(sample.region_pairs, [[0, 1], [0, 2], [1, 2]])
    np.testing.assert_allclose(sample.influence, [1.0, 1.0, 1.0])
    np.testing.assert_allclose(
        sample.vectors,
        [
            [[0.0, 0.0, 0.75], [0.0, 0.0, 0.0]],
            [[0.0, 0.0, 0.75], [-0.75, 0.0, 0.0]],
            [[0.0, 0.0, 0.0], [-0.75, 0.0, 0.0]],
        ],
    )


def test_boundary_warp_changes_influence_not_vector_query_coordinates() -> None:
    def affine_shear(plane_positions, iteration, axis, frequency):
        return plane_positions[:, 0] if axis == 0 else np.zeros(len(plane_positions))

    warp = ShearWarpField(
        ShearWarpConfig(iterations=1, amplitude=1.0, gain=1.0), affine_shear
    )
    field = _boundary_vectors(
        np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 2.0]]),
        width=0.5,
        warp=warp,
    )

    sample = field.sample(np.array([[-0.25, 0.25, 0.0]]))

    np.testing.assert_array_equal(sample.query_indices, [0])
    np.testing.assert_array_equal(sample.region_pairs, [[0, 1]])
    np.testing.assert_allclose(sample.influence, [1.0])
    np.testing.assert_allclose(
        sample.vectors, [[[-0.25, -0.25, 0.0], [-0.5, -0.5, 0.0]]]
    )


def test_composition_accepts_nonrotational_region_vector_sampler() -> None:
    regions = _regions(np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]))
    boundary = build_voronoi_boundary_field(regions, BoundaryInfluenceConfig(width=0.5))

    def linear_region_vectors(positions: np.ndarray, region_ids: np.ndarray):
        return np.column_stack(
            (
                positions[:, 0] + region_ids,
                2.0 * positions[:, 1],
                positions[:, 2] - region_ids,
            )
        )

    field = BoundaryVectorField(boundary, linear_region_vectors)
    sample = field.sample(np.array([[0.0, 1.0, 0.0]]))

    np.testing.assert_array_equal(sample.region_pairs, [[0, 1]])
    np.testing.assert_allclose(sample.vectors, [[[0.0, 2.0, 0.0], [1.0, 2.0, -1.0]]])


def test_empty_and_inactive_samples_return_typed_immutable_records() -> None:
    positions = np.empty((0, 3))
    zero_seed_regions = _regions(np.empty((0, 3)))
    one_seed_regions = _regions(np.array([[0.0, 0.0, 0.0]]))

    for regions, queries in (
        (zero_seed_regions, positions),
        (zero_seed_regions, np.array([[20.0, 20.0, 20.0]])),
        (one_seed_regions, positions),
        (one_seed_regions, np.array([[20.0, 20.0, 20.0]])),
    ):
        boundary = build_voronoi_boundary_field(
            regions, BoundaryInfluenceConfig(width=0.5)
        )
        field = BoundaryVectorField(
            boundary, lambda points, ids: np.zeros((len(ids), 3), dtype=np.float64)
        )
        sample = field.sample(queries)

        assert sample.query_indices.shape == (0,)
        assert sample.query_indices.dtype == np.int64
        assert sample.region_pairs.shape == (0, 2)
        assert sample.region_pairs.dtype == np.int64
        assert sample.influence.shape == (0,)
        assert sample.influence.dtype == np.float64
        assert sample.vectors.shape == (0, 2, 3)
        assert sample.vectors.dtype == np.float64
        _assert_read_only(sample)


def test_boundary_vector_sampling_is_batch_and_order_independent() -> None:
    field = _boundary_vectors(
        np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0]]),
        np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 2.0], [0.0, 0.0, 3.0]]),
        width=0.4,
    )
    points = np.random.default_rng(8).uniform(-1.0, 1.0, size=(1307, 3))
    full = field.sample(points)
    split = [
        (start, field.sample(points[start : start + 173]))
        for start in range(0, len(points), 173)
    ]
    split_indices = np.concatenate(
        [sample.query_indices + start for start, sample in split]
    )
    split_pairs = np.concatenate([sample.region_pairs for _, sample in split])
    split_influence = np.concatenate([sample.influence for _, sample in split])
    split_vectors = np.concatenate([sample.vectors for _, sample in split])
    order = np.random.default_rng(19).permutation(len(points))
    reordered = field.sample(points[order])
    original_indices = order[reordered.query_indices]
    stable_order = np.argsort(original_indices, kind="stable")

    np.testing.assert_array_equal(split_indices, full.query_indices)
    np.testing.assert_array_equal(split_pairs, full.region_pairs)
    np.testing.assert_array_equal(split_influence, full.influence)
    np.testing.assert_array_equal(split_vectors, full.vectors)
    np.testing.assert_array_equal(original_indices[stable_order], full.query_indices)
    np.testing.assert_array_equal(
        reordered.region_pairs[stable_order], full.region_pairs
    )
    np.testing.assert_array_equal(reordered.influence[stable_order], full.influence)
    np.testing.assert_array_equal(reordered.vectors[stable_order], full.vectors)
    for index in (0, 777, 1306):
        single = field.sample(points[index : index + 1])
        np.testing.assert_array_equal(
            single.query_indices, np.zeros(len(single.query_indices), dtype=np.int64)
        )
        np.testing.assert_array_equal(
            single.region_pairs, full.region_pairs[full.query_indices == index]
        )
        np.testing.assert_array_equal(
            single.influence, full.influence[full.query_indices == index]
        )
        np.testing.assert_array_equal(
            single.vectors, full.vectors[full.query_indices == index]
        )


def test_duplicate_query_points_keep_distinct_query_records() -> None:
    field = _boundary_vectors(
        np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 2.0]]),
        width=0.5,
    )

    sample = field.sample(np.array([[0.0, 1.0, 0.0], [0.0, 1.0, 0.0]]))

    np.testing.assert_array_equal(sample.query_indices, [0, 1])
    np.testing.assert_array_equal(sample.region_pairs, [[0, 1], [0, 1]])
    np.testing.assert_array_equal(sample.influence, [1.0, 1.0])
    np.testing.assert_array_equal(sample.vectors[0], sample.vectors[1])


def test_arbitrary_positions_and_compact_support_cutoff_are_pointwise() -> None:
    field = _boundary_vectors(
        np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 2.0]]),
        width=0.5,
    )
    points = np.array([[0.125, 0.37, -0.22], [0.0, 2.137, -3.41]])
    sample = field.sample(points)

    np.testing.assert_array_equal(sample.query_indices, [0, 1])
    np.testing.assert_allclose(sample.influence, [0.84375, 1.0])
    np.testing.assert_allclose(
        sample.vectors,
        [
            [[-0.37, 0.125, 0.0], [-0.74, 0.25, 0.0]],
            [[-2.137, 0.0, 0.0], [-4.274, 0.0, 0.0]],
        ],
    )

    epsilon = 1e-5
    edge = field.sample(
        np.array(
            [[0.5 - epsilon, 1.0, 0.0], [0.5, 1.0, 0.0], [0.5 + epsilon, 1.0, 0.0]]
        )
    )
    expected_influence = 3.0 * (2.0 * epsilon) ** 2 - 2.0 * (2.0 * epsilon) ** 3
    np.testing.assert_array_equal(edge.query_indices, [0])
    np.testing.assert_allclose(edge.influence, [expected_influence])
    assert np.max(np.abs(edge.influence[:, None, None] * edge.vectors)) < 1e-8

    np.testing.assert_array_equal(
        field.sample(points[1:2]).vectors, sample.vectors[1:2]
    )
    np.testing.assert_array_equal(
        field.sample(points[0:1]).vectors, sample.vectors[0:1]
    )
    unrelated = np.array([[100.0, 100.0, 100.0], [-100.0, 50.0, 3.0]])
    combined = field.sample(np.concatenate((unrelated, points[:1])))
    np.testing.assert_array_equal(combined.query_indices, [2])
    np.testing.assert_array_equal(combined.vectors, sample.vectors[:1])
