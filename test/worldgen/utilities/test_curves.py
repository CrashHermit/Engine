import numpy as np
import pytest

from src.worldgen.utilities.curves import smooth_upper_bound


def test_smooth_upper_bound_preserves_weak_values_and_exact_ceiling():
    values = np.array([0.0, 0.1, 0.8, 0.9, 1.0, 1.1, 3.0])
    bounded = smooth_upper_bound(values, upper=1.0, transition_half_width=0.1)
    np.testing.assert_array_equal(bounded[:4], values[:4])
    np.testing.assert_array_equal(bounded[-2:], [1.0, 1.0])
    assert 0.9 < bounded[4] < 1.0
    assert np.all(np.diff(bounded) >= 0.0)
    assert np.all((0.0 <= bounded) & (bounded <= 1.0))
    assert np.all(bounded <= values)


@pytest.mark.parametrize("join, expected_slope", [(0.9, 1.0), (1.1, 0.0)])
def test_smooth_upper_bound_has_matching_first_derivatives(join, expected_slope):
    step = 1e-6
    values = smooth_upper_bound(
        np.array([join - step, join, join + step]),
        upper=1.0,
        transition_half_width=0.1,
    )
    np.testing.assert_allclose(np.diff(values) / step, expected_slope, atol=1e-5)
