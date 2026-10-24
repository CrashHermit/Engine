from dataclasses import replace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world_field
from src.worldgen.geology.density import CrustDensityConfig, CrustDensityField


def test_continuous_geology_field_is_seeded_and_samples_arbitrary_positions():
    config = WorldgenConfig(seed=123)
    positions = np.array(
        [[0.0, 0.0, 0.0], [1.7, 0.2, -0.4], [-0.3, 1.2, 0.8]],
        dtype=np.float64,
    )
    first = generate_world_field(config)
    second = generate_world_field(config)
    other = generate_world_field(WorldgenConfig(seed=124))

    sample = first.geology.sample_source(positions).result
    repeated = second.geology.sample_source(positions).result
    different = other.geology.sample_source(positions).result
    for name in sample.__dataclass_fields__:
        np.testing.assert_array_equal(getattr(sample, name), getattr(repeated, name))
    assert not np.array_equal(sample.plate_ids, different.plate_ids)
    assert sample.plate_ids.dtype == np.int64
    assert sample.crust_region_ids.dtype == np.int64
    assert sample.continental_mask.dtype == bool
    for name in sample.__dataclass_fields__:
        assert not getattr(sample, name).flags.writeable


def test_field_generation_preserves_global_numpy_random_state():
    np.random.seed(77)
    before = np.random.get_state()
    field = generate_world_field(WorldgenConfig(seed=123))
    field.geology.sample_source(np.array([[0.0, 0.0, 0.0]]))
    after = np.random.get_state()

    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


def test_geology_material_density_and_pair_gradients_match_finite_differences():
    field = generate_world_field(WorldgenConfig(seed=321))
    point = np.array([[0.03, 0.08, -0.02]], dtype=np.float64)
    analytic = field.geology.sample_source_with_gradient(point)
    step = 1e-5
    for axis in range(3):
        offset = np.zeros_like(point)
        offset[0, axis] = step
        positive = field.geology.sample_source(point + offset)
        negative = field.geology.sample_source(point - offset)
        material_derivative = (
            positive.result.continental_weight[0]
            - negative.result.continental_weight[0]
        ) / (2.0 * step)
        np.testing.assert_allclose(
            analytic.continental_weight_gradients[0, axis],
            material_derivative,
            rtol=2e-4,
            atol=2e-6,
        )

    density = field.geology.density.sample_with_gradient(point)
    step = (
        2e-3  # Resolve float32 coordinates; the four-point stencil cancels curvature.
    )
    for axis in range(3):
        offset = np.zeros_like(point)
        offset[0, axis] = step
        positive = field.geology.density.sample(point + offset)[0]
        negative = field.geology.density.sample(point - offset)[0]
        outer_positive = field.geology.density.sample(point + 2 * offset)[0]
        outer_negative = field.geology.density.sample(point - 2 * offset)[0]
        numerical = (8 * (positive - negative) - (outer_positive - outer_negative)) / (
            12 * step
        )
        np.testing.assert_allclose(
            density.gradients[0, axis],
            numerical,
            rtol=2e-4,
            atol=2e-6,
        )


def test_crust_density_field_zero_strength_and_empty_samples_are_zero():
    field = CrustDensityField(CrustDensityConfig(variation_strength=0.0), noise_seed=17)
    positions = np.array([[0.1, -0.2, 0.3], [-0.4, 0.5, -0.6]])

    values = field.sample(positions)
    sample = field.sample_with_gradient(positions)
    np.testing.assert_array_equal(values, np.zeros(2))
    np.testing.assert_array_equal(sample.values, np.zeros(2))
    np.testing.assert_array_equal(sample.gradients, np.zeros((2, 3)))
    assert values.dtype == np.float64
    assert not values.flags.writeable

    empty = np.empty((0, 3), dtype=np.float64)
    assert field.sample(empty).shape == (0,)
    empty_sample = field.sample_with_gradient(empty)
    assert empty_sample.values.shape == (0,)
    assert empty_sample.gradients.shape == (0, 3)


def test_density_variation_changes_coastal_relief_without_changing_geology():
    base_config = WorldgenConfig(seed=2718)
    uniform_density_config = replace(
        base_config,
        geology=replace(
            base_config.geology,
            density=replace(base_config.geology.density, variation_strength=0.0),
        ),
    )
    varied = generate_world_field(base_config)
    uniform = generate_world_field(uniform_density_config)
    positions = np.random.default_rng(991).uniform(-0.9, 0.9, size=(96, 3))

    varied_geology = varied.geology.sample_source(positions)
    uniform_geology = uniform.geology.sample_source(positions)
    for name in varied_geology.result.__dataclass_fields__:
        np.testing.assert_array_equal(
            getattr(varied_geology.result, name), getattr(uniform_geology.result, name)
        )
    for name in varied_geology.motion.__dataclass_fields__:
        np.testing.assert_array_equal(
            getattr(varied_geology.motion, name), getattr(uniform_geology.motion, name)
        )
    for name in varied_geology.context.__dataclass_fields__:
        np.testing.assert_array_equal(
            getattr(varied_geology.context, name),
            getattr(uniform_geology.context, name),
        )

    varied_coastal = varied.source_relief.coastal.sample(positions).elevation
    uniform_coastal = uniform.source_relief.coastal.sample(positions).elevation
    assert np.any(varied_coastal != uniform_coastal)


def test_fused_geology_samples_match_independent_apis_and_empty_queries():
    geology = generate_world_field(WorldgenConfig(seed=701)).geology
    positions = np.array(
        [[0.04, 0.08, -0.02], [-0.17, 0.11, 0.21], [0.23, -0.19, 0.07]]
    )

    fused = geology.sample_source(positions)
    with_gradient = geology.sample_source_with_gradient(positions)
    for name in fused.result.__dataclass_fields__:
        np.testing.assert_allclose(
            getattr(fused.result, name),
            getattr(with_gradient.sample.result, name),
            rtol=1e-10,
            atol=1e-12,
        )

    material = geology.material.sample(positions)
    material_gradient = geology.sample_continental_weight_with_gradient(positions)
    np.testing.assert_allclose(
        fused.result.continental_weight,
        material.continental_weight,
        rtol=1e-10,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        with_gradient.sample.result.continental_weight,
        material_gradient.values,
        rtol=1e-10,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        with_gradient.continental_weight_gradients,
        material_gradient.gradients,
        rtol=1e-10,
        atol=1e-12,
    )

    independent_motion = geology.motion.sample(positions)
    independent_context = geology.context.sample_pairs(positions, independent_motion)
    for name in fused.context.__dataclass_fields__:
        np.testing.assert_allclose(
            getattr(fused.context, name),
            getattr(independent_context, name),
            rtol=1e-10,
            atol=1e-12,
        )
        np.testing.assert_allclose(
            getattr(with_gradient.sample.context, name),
            getattr(independent_context, name),
            rtol=1e-10,
            atol=1e-12,
        )

    empty = np.empty((0, 3), dtype=np.float64)
    empty_fused = geology.sample_source(empty)
    empty_gradient = geology.sample_source_with_gradient(empty)
    for name in empty_fused.result.__dataclass_fields__:
        assert getattr(empty_fused.result, name).shape == (0,)
        np.testing.assert_array_equal(
            getattr(empty_fused.result, name),
            getattr(empty_gradient.sample.result, name),
        )
    empty_material_gradient = geology.sample_continental_weight_with_gradient(empty)
    assert empty_material_gradient.values.shape == (0,)
    assert empty_material_gradient.gradients.shape == (0, 3)
    assert empty_gradient.continental_weight_gradients.shape == (0, 3)
    empty_motion = geology.motion.sample(empty)
    empty_context = geology.context.sample_pairs(empty, empty_motion)
    for name in empty_fused.context.__dataclass_fields__:
        assert getattr(empty_fused.context, name).shape == (0,)
        np.testing.assert_array_equal(
            getattr(empty_fused.context, name), getattr(empty_context, name)
        )
