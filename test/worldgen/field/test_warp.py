import numpy as np

from src.worldgen.field.noise import NoiseConfig
from src.worldgen.field.noise_warp import build_noise_shear_warp
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField


def test_noise_warped_voronoi_queries_are_deterministic_across_batches():
    from src.worldgen.field.voronoi import VoronoiField3D

    positions = np.random.default_rng(4).random((1307, 3))
    noise_config = NoiseConfig(octaves=3, base_frequency=1.2)
    warp_config = ShearWarpConfig(
        iterations=3, amplitude=0.18, lacunarity=1.7, gain=0.65
    )

    def make_warp(seed):
        return build_noise_shear_warp(noise_config, warp_config, seed=seed)

    seed_source = np.random.default_rng(22).random((32, 3))
    seeds_before = seed_source.copy()
    field = VoronoiField3D(seed_source)
    seed_source[:] = 0.0
    np.testing.assert_array_equal(field.seeds, seeds_before)
    assert not field.seeds.flags.writeable

    before = np.random.get_state()
    warp = make_warp(2026)
    warped = warp.sample(positions)
    samples = field.sample(warped)
    repeated_warped = make_warp(2026).sample(positions)
    repeated_samples = field.sample(repeated_warped)
    other_warped = make_warp(2027).sample(positions)
    after = np.random.get_state()

    np.testing.assert_array_equal(warped, repeated_warped)
    assert not np.array_equal(warped, other_warped)
    np.testing.assert_array_equal(samples.owner_seed_id, repeated_samples.owner_seed_id)

    order = np.array([1306, 0, 777, 1, 1024, 39])
    subset_warped = make_warp(2026).sample(positions[order])
    subset = field.sample(subset_warped)
    singleton = field.sample(make_warp(2026).sample(positions[777:778]))
    np.testing.assert_array_equal(subset.owner_seed_id, samples.owner_seed_id[order])
    np.testing.assert_array_equal(
        singleton.owner_seed_id, samples.owner_seed_id[777:778]
    )

    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]
    assert not np.shares_memory(warped, positions)
    np.testing.assert_array_equal(positions, np.random.default_rng(4).random((1307, 3)))


def test_multiscale_shears_and_inverse_use_updated_coordinates():
    def shear(plane_positions, iteration, axis, frequency_multiplier):
        return frequency_multiplier * plane_positions[:, 0]

    field = ShearWarpField(
        ShearWarpConfig(iterations=2, amplitude=0.5, lacunarity=2.0, gain=0.5),
        shear,
    )
    positions = np.array([[1.0, 2.0, 3.0], [4.0, -2.0, 0.5]])
    warped = field.sample(positions)
    expected = np.array([[3.5, 4.75, 5.75], [2.75, 0.875, 3.375]])
    np.testing.assert_allclose(warped, expected, atol=1e-12, rtol=0.0)
    np.testing.assert_allclose(field.inverse(warped), positions, atol=1e-12, rtol=0.0)

    source_points = np.array([[-4.0, 0.2, 7.0], [2.5, 3.25, -1.5]])
    np.testing.assert_allclose(
        field.sample(field.inverse(source_points)),
        source_points,
        atol=1e-12,
        rtol=0.0,
    )


def test_nonlinear_shears_are_invertible_batch_independently_without_projection():
    def shear(plane_positions, iteration, axis, frequency_multiplier):
        return np.sin(frequency_multiplier * plane_positions[:, 0]) + 0.5 * np.cos(
            frequency_multiplier * plane_positions[:, 1]
        )

    field = ShearWarpField(
        ShearWarpConfig(iterations=4, amplitude=0.48, lacunarity=1.7, gain=0.65),
        shear,
    )
    positions = np.random.default_rng(812).uniform(-3.0, 3.0, (1307, 3))
    original = positions.copy()
    warped = field.sample(positions)
    np.testing.assert_allclose(field.inverse(warped), positions, atol=1e-10, rtol=0.0)
    np.testing.assert_allclose(
        field.sample(field.inverse(positions)), positions, atol=1e-10, rtol=0.0
    )
    np.testing.assert_array_equal(positions, original)
    assert np.any(np.abs(warped) > 1.0)
    assert not np.allclose(np.linalg.norm(warped, axis=1), 1.0)

    split = np.concatenate(
        (field.sample(positions[:401]), field.sample(positions[401:]))
    )
    np.testing.assert_allclose(split, warped, atol=1e-10, rtol=0.0)
    order = np.random.default_rng(17).permutation(len(positions))
    reordered = field.sample(positions[order])
    np.testing.assert_allclose(reordered, warped[order], atol=1e-10, rtol=0.0)
    singleton = np.vstack([field.sample(point[None, :]) for point in positions])
    np.testing.assert_allclose(singleton, warped, atol=1e-10, rtol=0.0)
    duplicated = field.sample(np.concatenate((positions, positions[[7, 7]])))
    np.testing.assert_allclose(duplicated[:-2], warped, atol=1e-10, rtol=0.0)
    np.testing.assert_array_equal(duplicated[-2:], warped[[7, 7]])


def test_shear_identity_cases_return_owned_writable_float64_copies():
    def shear(plane_positions, iteration, axis, frequency_multiplier):
        return plane_positions[:, 0]

    positions = np.array([[1, 2, 3], [-4, 5, 6]], dtype=np.int64)
    empty = np.empty((0, 3), dtype=np.int64)
    fields = (
        ShearWarpField(ShearWarpConfig(iterations=0), shear),
        ShearWarpField(ShearWarpConfig(iterations=3, amplitude=0.0), shear),
    )
    for field in fields:
        for transform in (field.sample, field.inverse):
            result = transform(positions)
            np.testing.assert_array_equal(result, positions)
            assert result.dtype == np.float64
            assert result.flags.owndata and result.flags.writeable
            assert not np.shares_memory(result, positions)

            empty_result = transform(empty)
            assert empty_result.shape == (0, 3)
            assert empty_result.dtype == np.float64
            assert empty_result.flags.owndata and empty_result.flags.writeable
            for transform in (
                field.sample_with_jacobian,
                field.inverse_with_jacobian,
            ):
                result = transform(positions)
                np.testing.assert_array_equal(result.values, positions)
                np.testing.assert_array_equal(
                    result.jacobians, np.broadcast_to(np.eye(3), (2, 3, 3))
                )
                empty_result = transform(empty)
                assert empty_result.values.shape == (0, 3)
                assert empty_result.jacobians.shape == (0, 3, 3)

            assert not np.shares_memory(empty_result, empty)


def test_noise_warp_jacobians_match_finite_difference_and_inverse():
    points = np.random.default_rng(16).normal(size=(4, 3)) * 0.2
    warp = build_noise_shear_warp(
        NoiseConfig(octaves=2, base_frequency=0.7),
        ShearWarpConfig(iterations=2, amplitude=0.13),
        seed=87,
    )
    forward = warp.sample_with_jacobian(points)
    inverse = warp.inverse_with_jacobian(forward.values)
    epsilon = 5e-3
    for axis in range(3):
        displacement = np.eye(3)[axis] * epsilon
        finite = (
            warp.sample(points + displacement) - warp.sample(points - displacement)
        ) / (2.0 * epsilon)
        np.testing.assert_allclose(
            forward.jacobians[:, :, axis], finite, atol=5e-3, rtol=2e-2
        )
    np.testing.assert_allclose(inverse.values, points, atol=1e-12)
    np.testing.assert_allclose(
        inverse.jacobians @ forward.jacobians,
        np.broadcast_to(np.eye(3), (4, 3, 3)),
        atol=1e-10,
    )
    np.testing.assert_allclose(np.linalg.det(forward.jacobians), 1.0, atol=1e-10)
