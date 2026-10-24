import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.relief.coastal import SourceCoastalConfig, SourceCoastalField
from src.worldgen.relief.variation import TerrainVariationConfig, TerrainVariationField
from src.worldgen.relief.volcanism import VolcanicField, VolcanismConfig
from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.rod import RodScalarField
from src.worldgen.generate import generate_world_field


def _finite_difference(sample, points, step=1e-6):
    gradients = np.empty((len(points), 3), dtype=np.float64)
    for axis in range(3):
        delta = np.zeros_like(points)
        delta[:, axis] = step
        gradients[:, axis] = (sample(points + delta) - sample(points - delta)) / (
            2.0 * step
        )
    return gradients


def test_coastal_gradient_includes_weight_density_and_spatial_width_variation():
    def weights(points):
        return 0.53 + 0.08 * points[:, 0] - 0.04 * points[:, 2]

    def weight_gradient(points):
        return ScalarSample(
            weights(points), np.tile([0.08, 0.0, -0.04], (len(points), 1))
        )

    def density(points):
        return 0.2 * points[:, 1] + 0.1 * points[:, 2]

    def density_gradient(points):
        return ScalarSample(density(points), np.tile([0.0, 0.2, 0.1], (len(points), 1)))

    field = SourceCoastalField(
        sample_continental_weight=weights,
        sample_density_anomaly=density,
        influence_span_noise_seeds=(13, 29, 47),
        config=SourceCoastalConfig(),
        sample_continental_weight_with_gradient=weight_gradient,
        sample_density_anomaly_with_gradient=density_gradient,
    )
    points = np.array([[0.13, -0.11, 0.08], [-0.17, 0.19, -0.04]])
    gradient = field.sample_with_gradient(points)
    expected = _finite_difference(
        lambda q: field.sample(q).elevation, points, step=1e-4
    )
    np.testing.assert_allclose(gradient.gradients, expected, rtol=2e-5, atol=2e-7)

    empty = field.sample_with_gradient(np.empty((0, 3)))
    assert empty.values.shape == (0,)
    assert empty.gradients.shape == (0, 3)


def test_rod_gradient_covers_centerline_caps_support_and_spatial_modulation():
    def multiplier(points, scale):
        values = 1.0 + scale * points[:, 0]
        return ScalarSample(values, np.tile([scale, 0.0, 0.0], (len(points), 1)))

    field = RodScalarField(
        directions=np.array([[0.0, 0.0, 1.0]]),
        widths=np.array([0.3]),
        lengths=np.array([1.0]),
        heights=np.array([0.8]),
        taper_fraction=0.2,
        profile_power=2.0,
        sample_width_multiplier=lambda q: multiplier(q, 0.2).values,
        sample_width_multiplier_gradient=lambda q: multiplier(q, 0.2),
        sample_length_multiplier=lambda q: multiplier(q, -0.1).values,
        sample_length_multiplier_gradient=lambda q: multiplier(q, -0.1),
        sample_height_multiplier=lambda q: multiplier(q, 0.15).values,
        sample_height_multiplier_gradient=lambda q: multiplier(q, 0.15),
    )
    points = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.5],
            [0.05, 0.0, 0.06],
            [0.0, 0.0, 0.99],
            [0.34, 0.0, 0.5],
        ]
    )
    sampled = field.sample_with_gradient(points)
    expected = _finite_difference(field.sample, points, step=1e-8)
    np.testing.assert_allclose(sampled.gradients, expected, rtol=2e-4, atol=2e-6)
    np.testing.assert_allclose(sampled.gradients[0, :2], [0.0, 0.0], atol=1e-12)

    empty = field.sample_with_gradient(np.empty((0, 3)))
    assert empty.values.shape == (0,)
    assert empty.gradients.shape == (0, 3)


def test_terrain_variation_gradient_and_empty_query():
    field = TerrainVariationField(TerrainVariationConfig(), noise_seed=119)
    points = np.array([[0.31, -0.14, 0.27], [-0.2, 0.11, 0.42]])
    sampled = field.sample_fraction_with_gradient(points)
    # Float32 octave offsets cannot resolve tiny finite-difference displacements.
    expected = _finite_difference(field.sample_fraction, points, step=1e-3)
    assert np.linalg.norm(sampled.gradients - expected) < 0.015 * np.linalg.norm(
        sampled.gradients
    )
    empty = field.sample_fraction_with_gradient(np.empty((0, 3)))
    assert empty.values.shape == (0,)
    assert empty.gradients.shape == (0, 3)


def test_volcanic_gradient_matches_fixed_world_rods_and_empty_query():
    geology = generate_world_field(WorldgenConfig(seed=2026)).geology
    field = VolcanicField(
        sample_relief_inputs=geology.sample_relief_inputs,
        sample_relief_inputs_with_gradient=geology.sample_relief_inputs_with_gradient,
        noise_seed=7881,
        warp=geology.regions.warp,
        config=VolcanismConfig(candidate_count=128, hotspot_count=5, tectonic_count=5),
    )
    points = np.array([[0.41, -0.12, 0.73], [-0.32, 0.54, 0.26]])
    direction = field.hotspots.directions[0]
    across = np.cross(direction, [0.0, 0.0, 1.0])
    if np.linalg.norm(across) < 1e-8:
        across = np.cross(direction, [0.0, 1.0, 0.0])
    across /= np.linalg.norm(across)
    points = np.vstack(
        (points, 0.5 * direction + 0.3 * field.hotspots.widths[0] * across)
    )
    sampled = field.sample_with_gradient(points)
    for actual, selector in (
        (sampled.strength, lambda value: value.strength),
        (sampled.relief, lambda value: value.relief),
    ):
        expected = _finite_difference(
            lambda q: selector(field.sample(q)), points, step=1e-4
        )
        np.testing.assert_allclose(actual.gradients, expected, rtol=3e-3, atol=3e-6)
    empty = field.sample_with_gradient(np.empty((0, 3)))
    assert empty.strength.gradients.shape == (0, 3)
    assert empty.relief.gradients.shape == (0, 3)
