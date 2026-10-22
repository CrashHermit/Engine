import numpy as np

from src.worldgen.field.boundary_motion import BoundaryMotionConfig, BoundaryMotionField
from src.worldgen.field.boundary_vector import BoundaryVectorField
from src.worldgen.field.motion import RegionRotationField
from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.region_overlap import RegionOverlapField
from src.worldgen.field.voronoi import VoronoiField3D


def _field(seeds, omega, width=0.5, smoothing_width=0.01):
    partition = VoronoiField3D(np.asarray(seeds, dtype=float))
    influence = RegionInfluenceField(
        partition, RegionInfluenceConfig(transition_half_width=width)
    )
    overlap = RegionOverlapField(influence)
    rotations = RegionRotationField(partition, np.asarray(omega, dtype=float))
    return BoundaryMotionField(
        BoundaryVectorField(
            overlap, rotations.sample_regions, rotations.sample_regions_with_jacobian
        ),
        BoundaryMotionConfig(opening_smoothing_width=smoothing_width),
    )


def test_source_motion_uses_plane_distance_and_algebraic_overlap():
    field = _field([[-1, 0, 0], [1, 0, 0]], [[0, 0, 1], [0, 0, 2]])
    sample = field.sample(np.array([[0, 1, 0], [0.25, 1, 0], [0.5, 1, 0], [1, 1, 0.0]]))
    np.testing.assert_array_equal(sample.query_indices, [0, 1])
    np.testing.assert_allclose(sample.plane_distance, [0, 0.25])
    np.testing.assert_allclose(sample.influence, [1, 0.52734375])
    np.testing.assert_allclose(sample.normals, [[1, 0, 0], [1, 0, 0]])
    np.testing.assert_allclose(sample.convergence, [1, 1])
    np.testing.assert_allclose(sample.divergence, [0.01 * np.log1p(np.exp(-100))] * 2)
    assert sample.shear[0] == 0.0
    assert 0.24 < sample.shear[1] < 0.25


def test_volumetric_motion_components_are_not_projected_to_sphere():
    field = _field([[1, 0, 0], [0, 2, 0]], [[1, 0, 0], [0, 1, 0]])
    sample = field.sample(np.array([[0.5, 1, 1.0]]))
    np.testing.assert_allclose(sample.normals, [[-1 / np.sqrt(5), 2 / np.sqrt(5), 0]])
    np.testing.assert_allclose(sample.divergence, [1 / np.sqrt(5)], atol=1e-12)
    assert 0.0 < sample.convergence[0] < 1e-18
    raw_sliding = 9 / (2 * np.sqrt(5))
    assert raw_sliding - field.config.shear_smoothing < sample.shear[0] < raw_sliding


def test_seed_axis_bias_fixture_produces_shear_and_opposite_normal_sides():
    equal = _field([[1, 0, 0], [0, 1, 0]], [[1, 0, 0], [0, 1, 0]])
    sample = equal.sample(np.array([[0.5, 0.5, 0.4]]))
    np.testing.assert_allclose(sample.convergence, [0.01 * np.log(2.0)])
    np.testing.assert_allclose(sample.divergence, [0.01 * np.log(2.0)])
    raw_sliding = np.sqrt(1.32)
    assert raw_sliding - equal.config.shear_smoothing < sample.shear[0] < raw_sliding
    unequal = _field([[1, 0, 0], [0, 1, 0]], [[1, 0, 0], [0, 2, 0]])
    sides = unequal.sample(np.array([[0.5, 0.5, 1], [0.5, 0.5, -1.0]]))
    np.testing.assert_allclose(sides.opening, [-1 / np.sqrt(2), 1 / np.sqrt(2)])


def test_smooth_opening_split_preserves_signed_motion():
    field = _field(
        [[1, 0, 0], [0, 1, 0]],
        [[1, 0, 0], [0, 1, 0]],
        smoothing_width=0.1,
    )
    neutral = field.sample(np.array([[0.5, 0.5, 0.4]]))
    expected_neutral = 0.1 * np.log(2.0)
    np.testing.assert_allclose(neutral.convergence, [expected_neutral])
    np.testing.assert_allclose(neutral.divergence, [expected_neutral])
    np.testing.assert_allclose(
        neutral.divergence - neutral.convergence, neutral.opening
    )

    unequal = _field(
        [[1, 0, 0], [0, 1, 0]],
        [[1, 0, 0], [0, 2, 0]],
        smoothing_width=0.1,
    )
    sides = unequal.sample(np.array([[0.5, 0.5, 1], [0.5, 0.5, -1.0]]))
    np.testing.assert_array_less(np.zeros(2), sides.convergence + sides.divergence)
    np.testing.assert_allclose(sides.divergence - sides.convergence, sides.opening)


def test_motion_block_split_and_empty_samples():
    field = _field(
        [[-1, 0, 0], [1, 0, 0], [0, 2, 0]], [[0, 0, 1], [0, 0, 2], [0, 0, 3]], 0.4
    )
    points = np.random.default_rng(812).uniform(-1, 1, (1307, 3))
    whole = field.sample(points)
    starts = range(0, len(points), 101)
    parts = [field.sample(points[i : i + 101]) for i in starts]
    indices = np.concatenate(
        [part.query_indices + i for i, part in zip(range(0, len(points), 101), parts)]
    )
    np.testing.assert_array_equal(indices, whole.query_indices)
    for name in (
        "region_pairs",
        "plane_distance",
        "influence",
        "normals",
        "opening",
        "convergence",
        "divergence",
        "shear",
    ):
        values = getattr(whole, name)
        np.testing.assert_array_equal(
            np.concatenate([getattr(part, name) for part in parts]), values
        )
        assert not values.flags.writeable
    empty = field.sample(np.empty((0, 3)))
    assert empty.opening.shape == (0,)


def test_queries_preserve_seed_poles_positions_and_global_rng_state():
    seeds = np.array([[-1.0, 0, 0], [1.0, 0, 0]])
    angular_velocity = np.array([[0.0, 0, 1], [0.0, 0, 2]])
    positions = np.array([[0.0, 0.75, 0.2], [0.25, 1.0, -0.3]])
    seeds_before = seeds.copy()
    angular_before = angular_velocity.copy()
    positions_before = positions.copy()
    rng_before = np.random.get_state()

    field = _field(seeds, angular_velocity)
    field.sample(positions)

    rng_after = np.random.get_state()
    np.testing.assert_array_equal(seeds, seeds_before)
    np.testing.assert_array_equal(angular_velocity, angular_before)
    np.testing.assert_array_equal(positions, positions_before)
    assert rng_before[0] == rng_after[0]
    np.testing.assert_array_equal(rng_before[1], rng_after[1])
    assert rng_before[2:] == rng_after[2:]


def test_motion_gradients_match_centered_differences_and_zero_at_zero_velocity():
    field = _field(
        [[-1, 0, 0], [1, 0, 0], [0, 2, 0]],
        [[0.2, -0.1, 0.3], [-0.1, 0.4, 0.2], [0.3, 0.1, -0.2]],
        width=0.8,
    )
    point = np.array([[0.03, 0.12, -0.2]])
    sample = field.sample_with_gradient(point)
    step = 1e-6
    for component, gradients in (
        ("opening", sample.opening_gradients),
        ("convergence", sample.convergence_gradients),
        ("divergence", sample.divergence_gradients),
        ("shear", sample.shear_gradients),
        ("influence", sample.influence_gradients),
    ):
        numerical = np.empty_like(gradients)
        for axis in range(3):
            offset = np.zeros_like(point)
            offset[0, axis] = step
            positive = getattr(field.sample(point + offset), component)
            negative = getattr(field.sample(point - offset), component)
            numerical[:, axis] = (positive - negative) / (2.0 * step)
        np.testing.assert_allclose(gradients, numerical, rtol=2e-5, atol=2e-7)

    still = _field([[-1, 0, 0], [1, 0, 0]], [[0, 0, 0], [0, 0, 0]])
    zero = still.sample_with_gradient(np.array([[0.0, 0.0, 0.0]]))
    np.testing.assert_array_equal(zero.shear_gradients, np.zeros((1, 3)))
    outside = field.sample_with_gradient(np.array([[4.0, 0.0, 0.0]]))
    assert outside.sample.query_indices.size == 0
    assert outside.influence_gradients.shape == (0, 3)
