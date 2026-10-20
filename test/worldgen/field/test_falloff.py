import numpy as np

from src.worldgen.field.falloff import compact_influence


def test_compact_influence_has_cubic_endpoints_and_monotone_taper():
    distances = np.array([0.0, 0.125, 0.25, 0.375, 0.5, 0.75])

    influence = compact_influence(distances, width=0.5)

    np.testing.assert_allclose(influence, [1.0, 0.84375, 0.5, 0.15625, 0.0, 0.0])
    assert np.all(np.diff(influence) <= 0.0)
    assert influence.dtype == np.float64
    assert not influence.flags.writeable


def test_compact_influence_has_zero_first_derivative_at_support_endpoints():
    width = 0.5
    step = 1e-6
    at_start = compact_influence(np.array([0.0, step]), width=width)
    at_end = compact_influence(np.array([width - step, width]), width=width)

    assert abs((at_start[1] - at_start[0]) / step) < 1e-3
    assert abs((at_end[1] - at_end[0]) / step) < 1e-3


def test_compact_influence_preserves_empty_shape_and_returns_float64():
    distances = np.empty((0, 3), dtype=np.int64)

    influence = compact_influence(distances, width=1.0)

    assert influence.shape == (0, 3)
    assert influence.dtype == np.float64
    assert not influence.flags.writeable
