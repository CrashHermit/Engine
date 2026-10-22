import numpy as np

from src.worldgen.elevation.profiles import collision_profile, divergent_profile
from src.worldgen.elevation.ridge_detail import RidgeDetailConfig, RidgeDetailField


def _one_sided_slope(function, point: float, step: float) -> tuple[float, float]:
    value = function(point)
    return (value - function(point - step)) / step, (
        function(point + step) - value
    ) / step


def test_collision_crest_has_flat_peak_and_compact_smooth_support():
    width = 2.0
    crest_width = 0.25
    profile = lambda distance: collision_profile(abs(distance), width, crest_width)[1]
    support = width * crest_width
    assert profile(0.0) == 1.0
    assert profile(support / 2.0) == 0.25
    assert profile(support) == profile(2.0 * support) == 0.0
    for join in (0.0, support, -support):
        left, right = _one_sided_slope(profile, join, 1e-6)
        np.testing.assert_allclose([left, right], 0.0, atol=1e-3)


def test_continental_rift_shoulder_preserves_broad_envelope_and_flat_joins():
    def profile(t: float) -> float:
        return divergent_profile(
            abs(t),
            1.0,
            True,
            axial_width_fraction=0.1,
            axial_depth_multiplier=0.0,
            shoulder_height_multiplier=1.0,
        )

    assert profile(0.0) == profile(1.0) == 0.0
    assert profile(0.5) == 0.5  # unit shoulder factor times broad smoothstep(0.5)
    for join in (0.0, 1.0, -1.0):
        left, right = _one_sided_slope(profile, join, 1e-6)
        np.testing.assert_allclose([left, right], 0.0, atol=1e-3)


def test_ridge_detail_smooths_triangular_profile_joins(monkeypatch):
    import src.worldgen.elevation.ridge_detail as ridge_detail

    monkeypatch.setattr(
        ridge_detail,
        "normalized_noise",
        lambda positions, config, *, seed: positions[:, 0],
    )
    field = RidgeDetailField(19, RidgeDetailConfig(sharpness=3.0))

    def profile(noise: float) -> float:
        return float(field.sample(np.array([[noise, 0.0, 0.0]]))[0])

    assert profile(0.0) == profile(1.0) == 0.0
    assert profile(0.5) == 1.0
    assert 0.0 <= min(profile(0.25), profile(0.75))
    np.testing.assert_allclose(profile(0.25), profile(0.75))
    for join in (0.0, 1.0):
        left, right = _one_sided_slope(profile, join, 1e-5)
        assert abs(left) < 1e-8
        assert abs(right) < 1e-8
    left, right = _one_sided_slope(profile, 0.5, 1e-5)
    assert abs(left) < 1e-3
    assert abs(right) < 1e-3
