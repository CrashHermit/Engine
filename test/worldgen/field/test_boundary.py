import numpy as np
import pytest

from src.worldgen.field.boundary import (
    BoundaryInfluenceConfig,
    build_voronoi_boundary_field,
)
from src.worldgen.field.regions import WarpedVoronoiField
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField


def _regions(seeds, warp=None):
    if warp is None:
        warp = ShearWarpField(
            ShearWarpConfig(iterations=0),
            lambda plane, iteration, axis, frequency: np.zeros(len(plane)),
        )
    return WarpedVoronoiField(warp=warp, voronoi=VoronoiField3D(seeds))


def test_collinear_partition_returns_independent_adjacent_face_influences():
    regions = _regions(np.array([[-1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]))
    field = build_voronoi_boundary_field(regions, BoundaryInfluenceConfig(width=0.75))

    sample = field.sample(
        np.array([[-0.5, 0.0, 0.0], [0.0, 0.0, 0.0], [0.5, 0.0, 0.0]])
    )

    np.testing.assert_array_equal(sample.region_pairs, [[0, 1], [1, 2]])
    np.testing.assert_allclose(
        sample.influence, [[1.0, 0.0], [7 / 27, 7 / 27], [0.0, 1.0]]
    )
    assert sample.region_pairs is field.geometry.region_pairs
    assert not sample.influence.flags.writeable


def test_influence_width_is_independent_of_seed_spacing_and_symmetric():
    positions = np.array(
        [[0.0, 0.0, 0.0], [0.25, 0.0, 0.0], [-0.25, 0.0, 0.0], [1.0, 0.0, 0.0]]
    )
    for seeds in (
        np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        np.array([[-0.01, 0.0, 0.0], [0.01, 0.0, 0.0]]),
    ):
        field = build_voronoi_boundary_field(
            _regions(seeds), BoundaryInfluenceConfig(width=0.5)
        )
        np.testing.assert_allclose(
            field.sample(positions).influence[:, 0], [1, 0.5, 0.5, 0]
        )


def test_triple_junction_retains_each_boundary_contribution_at_full_strength():
    seeds = np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0]])
    field = build_voronoi_boundary_field(
        _regions(seeds), BoundaryInfluenceConfig(width=0.25)
    )

    sample = field.sample(
        np.array([[0.0, 0.75, 0.0], [0.0, 1.0, 0.0], [0.1, 1.0, 0.0]])
    )

    np.testing.assert_allclose(sample.influence[0], np.ones(3))
    pair_index = np.flatnonzero(np.all(sample.region_pairs == [0, 1], axis=1))[0]
    np.testing.assert_allclose(sample.influence[1:, pair_index], [0.0, 0.0])
    assert len(sample.region_pairs) == 3


def test_warp_moves_boundary_and_its_influence_band_together():
    def shear(plane_positions, iteration, axis, frequency_multiplier):
        return plane_positions[:, 0] if axis == 0 else np.zeros(len(plane_positions))

    warp = ShearWarpField(ShearWarpConfig(iterations=1, amplitude=1.0), shear)
    field = build_voronoi_boundary_field(
        _regions(np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]), warp),
        BoundaryInfluenceConfig(width=0.5),
    )

    sample = field.sample(
        np.array(
            [[0.0, 0.0, 0.0], [-0.25, 0.25, 0.0], [0.0, 0.25, 0.0], [0.25, 0.25, 0.0]]
        )
    )

    np.testing.assert_allclose(sample.influence[:, 0], [1.0, 1.0, 0.5, 0.0])


def test_inverse_maps_source_face_and_band_into_world_queries():
    def shear(plane_positions, iteration, axis, frequency_multiplier):
        return plane_positions[:, 0] if axis == 0 else np.zeros(len(plane_positions))

    warp = ShearWarpField(ShearWarpConfig(iterations=1, amplitude=1.0), shear)
    field = build_voronoi_boundary_field(
        _regions(np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]), warp),
        BoundaryInfluenceConfig(width=0.5),
    )
    source = np.array([[0.0, 1.0, 0.0], [0.25, 1.0, 0.0], [0.5, 1.0, 0.0]])

    world = warp.inverse(source)
    sample = field.sample(world)

    np.testing.assert_allclose(
        world, [[-1.0, 1.0, 0.0], [-0.75, 1.0, 0.0], [-0.5, 1.0, 0.0]]
    )
    np.testing.assert_allclose(sample.influence[:, 0], [1.0, 0.5, 0.0])


def test_boundary_sampling_is_stable_across_batches_and_query_order():
    field = build_voronoi_boundary_field(
        _regions(np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0]])),
        BoundaryInfluenceConfig(width=0.4),
    )
    points = np.random.default_rng(8).uniform(-1.0, 1.0, size=(1307, 3))

    full = field.sample(points)
    split = np.concatenate(
        [
            field.sample(points[start : start + 173]).influence
            for start in range(0, len(points), 173)
        ]
    )
    order = np.array([1306, 0, 777, 1, 1024, 39])
    reordered = field.sample(points[order])
    empty = field.sample(np.empty((0, 3)))

    np.testing.assert_array_equal(split, full.influence)
    np.testing.assert_array_equal(reordered.influence, full.influence[order])
    np.testing.assert_array_equal(reordered.region_pairs, full.region_pairs)
    single = field.sample(points[777:778])
    assert full.influence.shape == (1307, len(full.region_pairs))
    np.testing.assert_array_equal(single.influence, full.influence[777:778])
    assert np.all((full.influence >= 0.0) & (full.influence <= 1.0))
    assert empty.influence.shape == (0, len(full.region_pairs))
    assert not full.influence.flags.writeable
    assert not empty.influence.flags.writeable
    with pytest.raises(ValueError):
        full.region_pairs[0, 0] = -1


def test_empty_and_single_seed_partitions_sample_empty_face_axes():
    points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    for seeds in (np.empty((0, 3)), np.array([[0.0, 0.0, 0.0]])):
        field = build_voronoi_boundary_field(
            _regions(seeds), BoundaryInfluenceConfig(width=0.5)
        )
        sample = field.sample(points)
        assert sample.region_pairs.shape == (0, 2)
        assert sample.influence.shape == (2, 0)
        assert sample.influence.dtype == np.float64
        assert not sample.region_pairs.flags.writeable
        assert not sample.influence.flags.writeable
