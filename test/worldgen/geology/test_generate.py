import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world_field


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

    density = field.geology.sample_density_anomaly_with_gradient(point)
    step = (
        2e-3  # Resolve float32 coordinates; the four-point stencil cancels curvature.
    )
    for axis in range(3):
        offset = np.zeros_like(point)
        offset[0, axis] = step
        positive = field.geology.sample_density_anomaly(point + offset)[0]
        negative = field.geology.sample_density_anomaly(point - offset)[0]
        outer_positive = field.geology.sample_density_anomaly(point + 2 * offset)[0]
        outer_negative = field.geology.sample_density_anomaly(point - 2 * offset)[0]
        numerical = (8 * (positive - negative) - (outer_positive - outer_negative)) / (
            12 * step
        )
        np.testing.assert_allclose(
            density.gradients[0, axis],
            numerical,
            rtol=2e-4,
            atol=2e-6,
        )
