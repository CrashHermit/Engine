import numpy as np

from src.worldgen.relief.collision import collision_profile
from src.worldgen.relief.divergence import divergent_profile
from src.worldgen.relief.fault import fault_profile
from src.worldgen.field.boundary_motion import BoundaryMotionField
from src.worldgen.field.boundary_response import BoundaryResponseField
from src.worldgen.field.boundary_vector import BoundaryVectorField
from src.worldgen.field.compose import WarpedScalarField
from src.worldgen.field.motion import RegionRotationField
from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.region_overlap import RegionOverlapField
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField


def _composition():
    partition = VoronoiField3D(np.array([[-1.0, 0, 0], [1.0, 0, 0]]))
    regions = RegionInfluenceField(partition, RegionInfluenceConfig(0.5))
    overlap = RegionOverlapField(regions)
    rotations = RegionRotationField(partition, np.array([[0.0, 0, 1], [0.0, 0, 2]]))
    motion = BoundaryMotionField(BoundaryVectorField(overlap, rotations.sample_regions))

    def response(points, sample):
        result = np.empty(len(sample.query_indices), dtype=np.float64)
        for index, (distance, convergence, divergence, shear, influence) in enumerate(
            zip(
                sample.plane_distance,
                sample.convergence,
                sample.divergence,
                sample.shear,
                sample.influence,
                strict=True,
            )
        ):
            unsigned_distance = abs(float(distance))
            broad, crest = collision_profile(unsigned_distance, 0.5, 0.2)
            divergent = divergent_profile(unsigned_distance, 0.5, continental=True)
            shear_shape = fault_profile(unsigned_distance, 0.5)
            result[index] = influence * (
                convergence * (0.65 * broad + 0.35 * crest)
                + divergence * divergent
                + 0.15 * shear * shear_shape
            )
        return result

    return regions, BoundaryResponseField(motion, response)


def test_profile_response_decays_smoothly_to_zero_at_overlap_support():
    _, source = _composition()
    points = np.array(
        [[0.0, 1, 0], [-0.25, 1, 0], [0.25, 1, 0], [-0.5, 1, 0], [0.5, 1, 0]]
    )
    values = source.sample(points)
    assert values[0] > values[1] == values[2] > values[3] == values[4] == 0.0
    step = 1e-5
    join_points = np.array([[0.5 - step, 1, 0], [0.5, 1, 0], [0.5 + step, 1, 0]])
    slopes = np.diff(source.sample(join_points)) / step
    np.testing.assert_allclose(slopes, 0.0, atol=1e-4)
    assert not values.flags.writeable


def test_source_and_warped_empty_and_block_sampling():
    warp = ShearWarpField(
        ShearWarpConfig(iterations=1, amplitude=1),
        lambda p, i, a, f: p[:, 0] if a == 0 else np.zeros(len(p)),
    )
    regions, source = _composition()
    final = WarpedScalarField(warp.sample, source.sample)
    points = np.random.default_rng(812).uniform(-1, 1, (1307, 3))
    full = final.sample(points)
    split = np.concatenate(
        [final.sample(points[i : i + 97]) for i in range(0, len(points), 97)]
    )
    np.testing.assert_array_equal(full, split)
    np.testing.assert_array_equal(final.sample(np.empty((0, 3))), np.empty(0))
