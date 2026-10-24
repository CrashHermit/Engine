import numpy as np

from src.worldgen.climate.circulation import CirculationConfig
from src.worldgen.climate.generate import generate_circulation_field
from src.worldgen.geometry.vector import (
    regularized_normalize,
    regularized_normalize_with_jacobian,
)


def test_regularized_vector_normalization_jacobian_is_with_respect_to_input() -> None:
    vectors = np.array([[0.2, -0.4, 0.7], [0.0, 0.0, 0.0]])
    smoothing = 0.3
    values, jacobians = regularized_normalize_with_jacobian(vectors, smoothing)
    np.testing.assert_allclose(
        values, regularized_normalize(vectors, smoothing), rtol=1e-15, atol=0.0
    )
    step = 1e-6
    numeric = np.empty_like(jacobians)
    for component in range(3):
        offset = np.zeros_like(vectors)
        offset[:, component] = step
        numeric[:, :, component] = (
            regularized_normalize(vectors + offset, smoothing)
            - regularized_normalize(vectors - offset, smoothing)
        ) / (2.0 * step)
    np.testing.assert_allclose(jacobians, numeric, rtol=1e-9, atol=1e-10)
    assert not values.flags.writeable
    assert not jacobians.flags.writeable


def _latitude_points(degrees: np.ndarray) -> np.ndarray:
    radians = np.deg2rad(degrees)
    return np.column_stack((np.cos(radians), np.zeros(len(radians)), np.sin(radians)))


def test_default_field_has_five_zones_and_immutable_samples() -> None:
    field = generate_circulation_field(CirculationConfig(), (0.0, 0.0, 1.0))
    latitudes = np.array([-90.0, -75.0, -45.0, 0.0, 45.0, 75.0, 90.0])

    sample = field.sample(_latitude_points(latitudes))

    np.testing.assert_allclose(sample.axial_coordinate, np.sin(np.deg2rad(latitudes)))
    np.testing.assert_allclose(
        sample.band_strength[[0, 2, 3, 4, 6]], [-1, 1, -1, 1, -1], atol=1e-14
    )
    np.testing.assert_array_equal(
        np.sign(sample.wind_vectors_m_s[1:-1, 1]), [-1, 1, -1, 1, -1]
    )
    expected_speed = (
        10.0
        * np.cos(np.deg2rad(latitudes))
        * np.abs(sample.band_strength)
        / np.sqrt(np.cos(np.deg2rad(latitudes)) ** 2 + 0.05**2)
    )
    np.testing.assert_allclose(
        np.linalg.norm(sample.wind_vectors_m_s, axis=1), expected_speed, atol=1e-14
    )
    assert not sample.axial_coordinate.flags.writeable
    assert not sample.band_strength.flags.writeable
    assert not sample.wind_vectors_m_s.flags.writeable
    assert not field.axis.direction.flags.writeable


def test_wave_reversals_and_extrema_on_the_unit_sphere() -> None:
    field = generate_circulation_field(CirculationConfig(), (0.0, 0.0, 1.0))
    latitudes = np.array([-90.0, -60.0, -45.0, -30.0, 0.0, 30.0, 45.0, 60.0, 90.0])
    points = _latitude_points(latitudes)
    sample = field.bands.sample_with_gradient(points)

    np.testing.assert_allclose(
        sample.values, [-1, 0, 1, 0, -1, 0, 1, 0, -1], atol=1e-14
    )
    np.testing.assert_allclose(sample.gradients[[0, 2, 4, 6, 8]], 0.0, atol=1e-13)
    np.testing.assert_allclose(
        sample.gradients[[1, 3, 5, 7], 2],
        [2 * np.sqrt(3) * np.pi, -2 * np.pi, 2 * np.pi, -2 * np.sqrt(3) * np.pi],
        atol=1e-13,
    )
    np.testing.assert_allclose(sample.gradients[:, :2], 0.0, atol=1e-14)


def test_wave_varies_inside_bands_and_continues_outside_unit_sphere() -> None:
    field = generate_circulation_field(CirculationConfig(), (0.0, 0.0, 1.0))
    points = np.zeros((7, 3))
    points[:, 2] = np.sqrt([0.0, 0.125, 0.375, 0.625, 0.875, 1.125, 1.25])
    diagonal = np.sqrt(0.5)
    np.testing.assert_allclose(
        field.bands.sample(points),
        [-1, -diagonal, diagonal, diagonal, -diagonal, -diagonal, 0],
        atol=1e-14,
    )
    np.testing.assert_allclose(field.bands.sample(-points), field.bands.sample(points))


def test_off_sphere_origin_and_axis_are_regular() -> None:
    field = generate_circulation_field(CirculationConfig(), (0.0, 0.0, 1.0))
    points = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.7], [3.0, 0.0, 0.0]])

    sample = field.sample(points)
    jacobian_sample = field.wind.sample_with_jacobian(points)

    np.testing.assert_array_equal(sample.wind_vectors_m_s[:2], np.zeros((2, 3)))
    np.testing.assert_array_equal(sample.axial_coordinate, [0.0, 0.7, 0.0])
    assert np.isfinite(sample.wind_vectors_m_s).all()
    assert np.isfinite(jacobian_sample.jacobians).all()


def test_wind_jacobian_matches_finite_differences_at_transition_and_axis() -> None:
    field = generate_circulation_field(CirculationConfig(), (0.0, 0.0, 1.0))
    points = np.array(
        [
            [0.83, 0.17, 0.5],
            [0.5, -0.2, np.sqrt(0.75)],
            [0.7, 0.1, 0.3],
            [-0.1, 0.7, -1.3],
            [1e-5, -2e-5, 0.1],
            [0.0, 0.0, 0.0],
        ]
    )
    analytic = field.wind.sample_with_jacobian(points)
    step = 1e-6
    numeric = np.empty_like(analytic.jacobians)
    for axis in range(3):
        offset = np.zeros((1, 3))
        offset[0, axis] = step
        numeric[:, :, axis] = (
            field.wind.sample(points + offset) - field.wind.sample(points - offset)
        ) / (2.0 * step)
    np.testing.assert_allclose(analytic.jacobians, numeric, rtol=2e-5, atol=2e-7)


def test_tilted_axis_covariance_and_reference_speed_scaling() -> None:
    rotation = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])
    points = _latitude_points(np.array([-75.0, -45.0, 0.0, 45.0, 75.0]))
    original = generate_circulation_field(CirculationConfig(), (0.0, 0.0, 1.0)).sample(
        points
    )
    tilted_axis = rotation @ np.array([0.0, 0.0, 1.0])
    tilted = generate_circulation_field(CirculationConfig(), tuple(tilted_axis)).sample(
        points @ rotation.T
    )
    faster = generate_circulation_field(
        CirculationConfig(base_speed_m_s=20.0), (0.0, 0.0, 1.0)
    ).sample(points)

    np.testing.assert_allclose(tilted.axial_coordinate, original.axial_coordinate)
    np.testing.assert_allclose(tilted.band_strength, original.band_strength)
    np.testing.assert_allclose(
        tilted.wind_vectors_m_s, original.wind_vectors_m_s @ rotation.T
    )
    np.testing.assert_allclose(faster.wind_vectors_m_s, 2.0 * original.wind_vectors_m_s)
