import numpy as np

from src.worldgen.utilities.smooth import smooth_maximum, smooth_minimum


def test_smooth_extrema_are_finite_and_broadcast_inputs():
    values = np.array([-2.0, 0.0, 2.0])
    maximum = smooth_maximum(values, 0.0, width=0.25)
    minimum = smooth_minimum(values, 0.0, width=0.25)

    assert maximum.shape == values.shape
    assert minimum.shape == values.shape
    assert np.all(np.isfinite(maximum))
    assert np.all(np.isfinite(minimum))
    np.testing.assert_allclose(minimum, -smooth_maximum(-values, 0.0, width=0.25))


def test_smooth_extrema_have_a_configured_neutral_transition():
    width = 0.1
    expected = width * np.log(2.0)

    np.testing.assert_allclose(smooth_maximum(0.0, 0.0, width=width), expected)
    np.testing.assert_allclose(smooth_minimum(0.0, 0.0, width=width), -expected)


def test_smooth_opening_channels_preserve_the_signed_difference():
    opening = np.array([-1.0, -0.05, 0.0, 0.05, 1.0])
    convergence = -smooth_minimum(opening, 0.0, width=0.01)
    divergence = smooth_maximum(opening, 0.0, width=0.01)

    np.testing.assert_allclose(divergence - convergence, opening)
    assert np.all(convergence >= 0.0)
    assert np.all(divergence >= 0.0)
