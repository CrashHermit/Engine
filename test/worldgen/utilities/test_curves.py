import numpy as np
import pytest

from src.worldgen.utilities.curves import (
    saturating_response,
    saturating_response_derivative,
    smooth_upper_bound,
)


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


def test_saturating_response_preserves_zero_sign_and_weak_motion():
    values = np.array([-1e-7, 0.0, 1e-7, -0.5, 0.5])
    scale = 2.0
    response = saturating_response(values, scale=scale)

    assert response[1] == 0.0
    np.testing.assert_array_equal(np.sign(response), np.sign(values))
    np.testing.assert_allclose(response[:3], values[:3] / scale, rtol=1e-14, atol=0.0)
    np.testing.assert_allclose(response[3:], values[3:] / np.hypot(values[3:], scale))


def test_saturating_response_has_bounded_strong_limit_and_sublinear_growth():
    values = np.array([1.0, 10.0, 1e6])
    scale = 0.5
    response = saturating_response(values, scale=scale)

    assert np.all((response >= 0.0) & (response < 1.0))
    assert response[2] > 0.999999
    assert response[1] - response[0] < values[1] - values[0]
    assert response[2] - response[1] < response[1] - response[0]
    np.testing.assert_allclose(response[-1], values[-1] / np.hypot(values[-1], scale))


def test_saturating_response_derivative_matches_analytic_curve():
    values = np.array([-8.0, -0.25, 0.0, 0.25, 8.0])
    scale = 1.5
    derivative = saturating_response_derivative(values, scale=scale)
    expected = scale**2 / np.hypot(values, scale) ** 3
    step = 1e-6
    numerical = (
        saturating_response(values + step, scale=scale)
        - saturating_response(values - step, scale=scale)
    ) / (2 * step)

    np.testing.assert_allclose(derivative, expected)
    np.testing.assert_allclose(derivative, numerical, rtol=2e-6, atol=1e-10)
    assert derivative[2] == 1.0 / scale
