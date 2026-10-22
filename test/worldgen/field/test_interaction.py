import numpy as np

from src.worldgen.field.boundary_motion import BoundaryMotionConfig, BoundaryMotionField
from src.worldgen.field.boundary_vector import BoundaryVectorField
from src.worldgen.field.compose import WarpedScalarField
from src.worldgen.field.interaction import BoundaryInteractionField
from src.worldgen.field.motion import RegionRotationField
from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.region_overlap import RegionOverlapField
from src.worldgen.field.regions import WarpedVoronoiField
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField


def _interaction(seeds, omega, width=0.25, warp=None):
    warp = warp or ShearWarpField(
        ShearWarpConfig(iterations=0), lambda p, i, a, f: np.zeros(len(p))
    )
    regions = WarpedVoronoiField(warp, VoronoiField3D(np.asarray(seeds, dtype=float)))
    influence = RegionInfluenceField(
        regions.voronoi, RegionInfluenceConfig(transition_half_width=width)
    )
    overlap = RegionOverlapField(influence)
    motion = BoundaryMotionField(
        BoundaryVectorField(
            overlap,
            RegionRotationField(
                regions.voronoi, np.asarray(omega, dtype=float)
            ).sample_regions,
        ),
        config=BoundaryMotionConfig(opening_smoothing_width=0.01),
    )
    return regions, BoundaryInteractionField(motion)


def test_junction_keeps_convergence_and_divergence_as_independent_channels():
    seeds = np.array([[-1, 0, 0], [1, 0, 0], [0, 2, 0]], dtype=float)
    warp = ShearWarpField(
        ShearWarpConfig(iterations=0), lambda p, i, a, f: np.zeros(len(p))
    )
    regions = WarpedVoronoiField(warp, VoronoiField3D(seeds))
    influence = RegionInfluenceField(
        regions.voronoi, RegionInfluenceConfig(transition_half_width=0.25)
    )
    overlap = RegionOverlapField(influence)
    vectors = np.array([[0, 0, 0], [1, 0, 0], [0, -1, 0]], dtype=float)

    def constant_region_vectors(positions, region_ids):
        return vectors[region_ids]

    motion = BoundaryMotionField(BoundaryVectorField(overlap, constant_region_vectors))
    field = BoundaryInteractionField(motion)
    points = np.array([[0, 0.75, 0.0]])
    sample = field.sample(points)
    np.testing.assert_allclose(sample.convergence, [4 / 9 * 3 / np.sqrt(5)])
    np.testing.assert_allclose(sample.divergence, [4.0 / 9.0])
    raw_sliding = 4.0 / 9.0 * 4.0 / np.sqrt(5)
    assert raw_sliding - 0.02 < sample.shear[0] < raw_sliding
    for name in ("convergence", "divergence", "shear"):
        np.testing.assert_array_equal(
            getattr(sample, name), getattr(field, f"sample_{name}")(points)
        )


def test_equal_region_velocities_have_zero_shear_and_smooth_opening_channels():
    seeds = np.array([[-1, 0, 0], [1, 0, 0], [0, 2, 0]], dtype=float)
    _, field = _interaction(seeds, [[0, 0, 1]] * 3, width=0.5)
    points = np.array([[0, 0.75, 0.0]])
    assert np.any(field.motion.sample(points).influence > 0.0)
    np.testing.assert_array_equal(field.sample_shear(points), [0.0])
    neutral = field.motion.config.opening_smoothing_width * np.log(2.0) * (4.0 / 3.0)
    np.testing.assert_allclose(field.sample_convergence(points), [neutral])
    np.testing.assert_allclose(field.sample_divergence(points), [neutral])


def test_warped_scalar_component_equals_source_component_at_warped_query():
    shear = lambda plane, iteration, axis, frequency: (
        plane[:, 0] if axis == 0 else np.zeros(len(plane))
    )
    warp = ShearWarpField(ShearWarpConfig(iterations=1, amplitude=1), shear)
    regions, field = _interaction(
        [[-1, 0, 0], [1, 0, 0]], [[0, 0, 1], [0, 0, 2]], warp=warp
    )
    world_points = np.array(
        [[-1, 1, 0], [-0.75, 1, 0], [-0.5, 1, 0], [0, 1, 0], [0.1, 0.3, 0.7]]
    )
    source_points = warp.sample(world_points)
    for name in ("convergence", "divergence", "shear"):
        source_sampler = getattr(field, f"sample_{name}")
        world_field = WarpedScalarField(warp.sample, source_sampler)
        np.testing.assert_allclose(
            world_field.sample(world_points), source_sampler(source_points)
        )


def test_interaction_empty_and_far_queries_are_zero():
    _, field = _interaction([[-1, 0, 0], [1, 0, 0]], [[0, 0, 1], [0, 0, 2]])
    points = np.array([[20.0, 20.0, 20.0]])
    for name in ("convergence", "divergence", "shear"):
        values = getattr(field, f"sample_{name}")(points)
        np.testing.assert_array_equal(values, [0])
        assert not values.flags.writeable
        assert getattr(field, f"sample_{name}")(np.empty((0, 3))).shape == (0,)
