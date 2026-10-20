import numpy as np
import pytest

from src.worldgen.field.noise import NoiseConfig
from src.worldgen.field.noise_warp import build_noise_shear_warp
from src.worldgen.field.warp import ShearWarpConfig


@pytest.mark.parametrize("seed", [123, 2026, 31415])
@pytest.mark.parametrize("amplitude", [0.24, 0.48])
def test_noise_shear_warp_roundtrips_deterministically_across_batches(seed, amplitude):
    noise_config = NoiseConfig(
        octaves=3, base_frequency=1.2, lacunarity=2.0, persistence=0.5
    )
    warp_config = ShearWarpConfig(
        iterations=4, amplitude=amplitude, lacunarity=1.7, gain=0.65
    )
    points = np.random.default_rng(812).uniform(-3.0, 3.0, (1307, 3))
    order = np.random.default_rng(seed).permutation(len(points))

    before = np.random.get_state()
    warp = build_noise_shear_warp(noise_config, warp_config, seed=seed)
    forward = warp.sample(points)
    restored = warp.inverse(forward)
    restored_from_source = warp.sample(warp.inverse(points))
    repeated = build_noise_shear_warp(noise_config, warp_config, seed=seed).sample(
        points
    )
    other_seed = build_noise_shear_warp(
        noise_config, warp_config, seed=seed + 1
    ).sample(points)
    after = np.random.get_state()

    np.testing.assert_allclose(restored, points, atol=1e-6, rtol=0.0)
    np.testing.assert_allclose(restored_from_source, points, atol=1e-6, rtol=0.0)
    np.testing.assert_array_equal(forward, repeated)
    assert not np.array_equal(forward, other_seed)
    np.testing.assert_array_equal(warp.sample(points[order]), forward[order])
    split_forward = np.concatenate(
        (warp.sample(points[:401]), warp.sample(points[401:]))
    )
    np.testing.assert_array_equal(split_forward, forward)
    singleton_forward = np.vstack([warp.sample(point[None, :]) for point in points])
    np.testing.assert_array_equal(singleton_forward, forward)
    duplicate_forward = warp.sample(np.concatenate((points, points[[7, 7]])))
    np.testing.assert_array_equal(duplicate_forward[:-2], forward)
    np.testing.assert_array_equal(duplicate_forward[-2:], forward[[7, 7]])

    inverse_again = warp.inverse(points)
    np.testing.assert_array_equal(warp.inverse(points), inverse_again)
    np.testing.assert_array_equal(warp.inverse(points[order]), inverse_again[order])
    split_inverse = np.concatenate(
        (warp.inverse(points[:401]), warp.inverse(points[401:]))
    )
    np.testing.assert_array_equal(split_inverse, inverse_again)
    singleton_inverse = np.vstack([warp.inverse(point[None, :]) for point in points])
    np.testing.assert_array_equal(singleton_inverse, inverse_again)
    duplicate_inverse = warp.inverse(np.concatenate((points, points[[7, 7]])))
    np.testing.assert_array_equal(duplicate_inverse[:-2], inverse_again)
    np.testing.assert_array_equal(duplicate_inverse[-2:], inverse_again[[7, 7]])

    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]
