import numpy as np

from src.worldgen.elevation.response import (
    collision_relief,
    continental_rift_relief,
    oceanic_ridge_relief,
    shear_relief,
    subduction_relief,
    transform_relief,
)
from src.worldgen.field.boundary_motion import BoundaryMotionField
from src.worldgen.field.boundary_response import BoundaryResponseField
from src.worldgen.field.boundary_vector import BoundaryVectorField
from src.worldgen.field.compose import WarpedScalarField
from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.region_overlap import RegionOverlapField
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField


RESPONSES = (
    collision_relief,
    continental_rift_relief,
    oceanic_ridge_relief,
    subduction_relief,
    shear_relief,
    transform_relief,
)


def test_profile_shapes_preserve_crests_trenches_and_axial_valleys():
    from src.worldgen.elevation.profiles import (
        collision_profile,
        divergent_profile,
        shear_profile,
        subduction_profile,
    )

    broad, crest = collision_profile(0.0, 4.0, 0.2)
    assert broad == 1.0
    assert crest == 1.0
    assert collision_profile(3.5, 4.0, 0.2)[1] == 0.0

    assert subduction_profile(-0.0, 4.0) == subduction_profile(0.0, 4.0)
    assert subduction_profile(-0.0, 4.0) < 0.0
    assert subduction_profile(1.0, 4.0) > 0.0
    assert subduction_profile(4.0, 4.0) == 0.0

    normal_trench = subduction_profile(-0.5, 4.0)
    deep_trench = subduction_profile(-0.5, 4.0, trench_depth_multiplier=4.0)
    np.testing.assert_allclose(deep_trench, normal_trench * 4.0)

    assert divergent_profile(0.0, 4.0, True) < 0.0
    assert divergent_profile(0.0, 4.0, False) > 0.0
    assert divergent_profile(4.0, 4.0, False) == 0.0

    assert shear_profile(0.0, 4.0) == 1.0
    assert shear_profile(4.0, 4.0) == 0.0


def test_collision_crest_and_divergent_landforms_have_distinct_shapes():
    distances = np.array([0.0, 0.125, 0.25, 0.5, 1.0, 1.1])
    strength = np.ones(len(distances))
    collision = collision_relief(distances, strength, 1.0, 2.0)
    rift = continental_rift_relief(distances, strength, 1.0, 2.0)
    ridge = oceanic_ridge_relief(distances, strength, 1.0, 2.0)
    np.testing.assert_allclose(collision[[0, 3, 4, 5]], [6, 1, 0, 0])
    assert rift[0] == -1.3
    assert rift[2] > 0
    assert 0 < ridge[0] < ridge[1] < ridge[2]
    np.testing.assert_array_equal(rift[-2:], [0, 0])
    np.testing.assert_array_equal(ridge[-2:], [0, 0])


def test_subduction_polarity_places_arc_only_on_overriding_side():
    distances = np.array([-1.0, -0.25, 0.0, 0.25, 1.0])
    relief = subduction_relief(distances, np.ones(5), 1.0, 2.0)
    np.testing.assert_allclose(relief, [0, 0, -2, 3, 0])
    reversed_polarity = subduction_relief(-distances, np.ones(5), 1.0, 2.0)
    np.testing.assert_array_equal(reversed_polarity, relief[::-1])


def test_response_strength_scaling_zero_motion_and_compact_support():
    distances = np.array([0.0, 0.05, 0.125, 0.4, 1.0, 1.5])
    strength = np.ones(len(distances))
    for response in RESPONSES:
        relief = response(distances, strength, 1.0, 2.0)
        np.testing.assert_allclose(
            response(distances, strength * 3, 1.0, 2.0), 3 * relief
        )
        np.testing.assert_array_equal(
            response(distances, strength * 0, 1.0, 2.0), np.zeros(6)
        )
        np.testing.assert_array_equal(relief[-2:], [0, 0])
        assert response(np.empty(0), np.empty(0), 1.0, 2.0).shape == (0,)
        edge = response(np.array([1 - 1e-7]), np.ones(1), 1.0, 2.0)
        assert abs(edge[0]) < 1e-6
    np.testing.assert_allclose(
        transform_relief(distances, -strength, 1.0, 2.0),
        -transform_relief(distances, strength, 1.0, 2.0),
    )


def test_subduction_and_shear_compose_per_pair_before_scalar_warp():
    regions = RegionInfluenceField(
        VoronoiField3D(np.array([[-1.0, 0, 0], [1.0, 0, 0]])),
        RegionInfluenceConfig(1.0),
    )
    overlap = RegionOverlapField(regions)
    velocities = np.array([[0.0, 0, 0], [-1.0, 1, 0]])
    motion = BoundaryMotionField(
        BoundaryVectorField(overlap, lambda positions, ids: velocities[ids])
    )

    def response(positions, sample):
        signed_distances = sample.plane_distance
        per_pair = subduction_relief(
            signed_distances, sample.convergence, 1.0, 2.0
        ) + shear_relief(np.abs(sample.plane_distance), sample.shear, 1.0, 0.1)
        return sample.influence * per_pair

    source = BoundaryResponseField(motion, response)
    warp = ShearWarpField(
        ShearWarpConfig(iterations=1, amplitude=1.0),
        lambda plane, iteration, axis, frequency: (
            plane[:, 0] if axis == 0 else np.zeros(len(plane))
        ),
    )
    world = WarpedScalarField(warp.sample, source.sample)
    positions = np.array([[-1.25, 1, 0], [-1.0, 1, 0], [-0.75, 1, 0], [0, 1, 0]])
    source_positions = warp.sample(positions)
    sample = motion.sample(source_positions)
    np.testing.assert_array_equal(sample.query_indices, [0, 1, 2])
    assert sample.influence[1] == 1.0
    assert np.any(source.sample(source_positions) != 0)
    np.testing.assert_array_equal(
        world.sample(positions), source.sample(source_positions)
    )
