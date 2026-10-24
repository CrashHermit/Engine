from dataclasses import replace
import numpy as np

from src.worldgen.field.boundary_motion import BoundaryMotionField, BoundaryMotionSample
from src.worldgen.field.boundary_vector import BoundaryVectorField
from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.region_overlap import RegionOverlapField
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.geology.crust_field import CrustField
from src.worldgen.geology.crust_influence import (
    CrustInfluenceField,
    MaterialBlendConfig,
    continental_response_weight,
)
from src.worldgen.geology.subduction_preference import (
    PolarityConfig,
    SubductionPreferenceField,
    overriding_weights,
)
from src.worldgen.geology.tectonic_context import TectonicContextField


def _motion_sample(region_pairs, *, convergence, divergence, influence):
    size = len(region_pairs)
    return BoundaryMotionSample(
        query_indices=np.arange(size, dtype=np.int64),
        region_pairs=np.asarray(region_pairs, dtype=np.int64).reshape((-1, 2)),
        plane_distance=np.full(size, 0.1),
        influence=np.asarray(influence, dtype=np.float64),
        normals=np.tile(np.array([[1.0, 0.0, 0.0]]), (size, 1)),
        opening=np.asarray(divergence) - np.asarray(convergence),
        convergence=np.asarray(convergence, dtype=np.float64),
        divergence=np.asarray(divergence, dtype=np.float64),
        shear=np.full(size, 0.25),
    )


def _context(directed):
    seeds = np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    regions = RegionInfluenceField(
        VoronoiField3D(seeds), RegionInfluenceConfig(transition_half_width=0.5)
    )
    crust = CrustField(regions.partition, np.array([False, True]))
    material = CrustInfluenceField(crust, regions)
    preference = SubductionPreferenceField(crust, regions)
    blend = MaterialBlendConfig(midpoint=0.4, transition_width=0.3)
    polarity = PolarityConfig(preference_scale=0.4, seeded_bias=0.15)
    pair_signs = np.array([[0.0, 1.0], [-1.0, 0.0]])
    context = TectonicContextField(
        material.sample,
        preference.sample,
        pair_signs,
        directed=directed,
        blend=blend,
        polarity=polarity,
        sample_material_gradient=material.sample_with_gradient,
        sample_preference_jacobian=preference.sample_with_jacobian,
    )
    return context, material, preference, regions, blend, polarity


def test_context_resolves_continuous_material_and_motion_for_ordered_pairs():
    positions = np.array([[-0.1, 0.0, 0.0], [0.1, 0.0, 0.0]])
    context, material_field, preference_field, _, blend, polarity = _context(
        directed=True
    )
    pair = np.array([0, 1])
    motion = _motion_sample(
        [pair, pair],
        convergence=[0.8, 0.0],
        divergence=[0.0, 0.6],
        influence=[0.7, 0.9],
    )

    sample = context.sample_pairs(positions, motion)
    material = material_field.sample(positions)
    expected_blend = continental_response_weight(
        material.continental_weight[motion.query_indices], blend
    )
    preference = preference_field.sample(positions)[motion.query_indices]
    expected_polarity = overriding_weights(
        np.einsum("ij,ij->i", preference, motion.normals),
        np.ones(2),
        directed=True,
        config=polarity,
    )
    np.testing.assert_allclose(sample.plane_distance, [0.1, 0.1])
    np.testing.assert_allclose(sample.continental_blend, expected_blend)
    np.testing.assert_allclose(sample.b_overrides_weight, expected_polarity)
    np.testing.assert_array_equal(sample.convergence, motion.convergence)
    np.testing.assert_array_equal(sample.divergence, motion.divergence)
    np.testing.assert_array_equal(sample.shear, motion.shear)
    np.testing.assert_array_equal(sample.influence, motion.influence)


def test_context_keeps_seeded_polarity_and_empty_pair_shapes():
    positions = np.array([[-0.1, 0.0, 0.0], [0.1, 0.0, 0.0]])
    context, _, _, _, _, _ = _context(directed=False)
    pair = np.array([0, 1])
    motion = _motion_sample(
        [pair, pair],
        convergence=[1.0, 1.0],
        divergence=[0.0, 0.0],
        influence=[1.0, 1.0],
    )
    sample = context.sample_pairs(positions, motion)
    np.testing.assert_array_equal(
        sample.b_overrides_weight,
        overriding_weights(
            np.zeros(2), np.ones(2), directed=False, config=context.polarity
        ),
    )
    np.testing.assert_array_equal(
        context.overriding_weights(positions, motion), sample.b_overrides_weight
    )

    empty_motion = _motion_sample([], convergence=[], divergence=[], influence=[])
    empty = context.sample_pairs(np.empty((0, 3)), empty_motion)
    assert empty.plane_distance.shape == (0,)
    assert empty.continental_blend.shape == (0,)
    assert empty.b_overrides_weight.shape == (0,)
    assert empty.convergence.shape == (0,)
    assert empty.divergence.shape == (0,)
    assert empty.shear.shape == (0,)
    assert empty.influence.shape == (0,)


def test_junction_context_reuses_full_query_preference_for_sparse_pairs():
    seeds = np.array(
        [
            [1.0, 0.0, 0.0],
            [-0.5, np.sqrt(3.0) / 2.0, 0.0],
            [-0.5, -np.sqrt(3.0) / 2.0, 0.0],
        ]
    )
    partition = VoronoiField3D(seeds)
    regions = RegionInfluenceField(partition, RegionInfluenceConfig(0.5))
    crust = CrustField(partition, np.array([True, False, True]))
    material = CrustInfluenceField(crust, regions)
    preference = SubductionPreferenceField(crust, regions)
    overlap = RegionOverlapField(regions)
    angular_velocity = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])
    motion_field = BoundaryMotionField(
        BoundaryVectorField(
            overlap,
            lambda points, region_ids: np.cross(angular_velocity[region_ids], points),
        )
    )
    positions = np.array([[0.0, 0.0, 0.0]])
    motion = motion_field.sample(positions)
    regional = regions.sample(positions)
    np.testing.assert_allclose(regional.weights, np.full((1, 3), 1.0 / 3.0))
    np.testing.assert_array_equal(motion.query_indices, [0, 0, 0])
    np.testing.assert_array_equal(motion.region_pairs, [[0, 1], [0, 2], [1, 2]])

    pair_signs = np.array([[0.0, 1.0, 1.0], [-1.0, 0.0, 1.0], [-1.0, -1.0, 0.0]])
    context = TectonicContextField(
        material.sample, preference.sample, pair_signs, directed=True
    )
    sampled = context.sample_pairs(positions, motion)
    material_sample = material.sample_from_regions(regional)
    preference_vectors = preference.sample_from_regions(positions, regional)
    supplied = context.sample_pairs(
        positions,
        motion,
        material_sample=material_sample,
        preference_vectors=preference_vectors,
    )
    expected_vector = np.array([[1.0 / 3.0, -np.sqrt(3.0) / 3.0, 0.0]])
    np.testing.assert_allclose(preference_vectors, expected_vector)
    pair_preference = np.einsum(
        "ij,ij->i",
        np.broadcast_to(expected_vector, motion.normals.shape),
        motion.normals,
    )
    expected = overriding_weights(
        pair_preference,
        pair_signs[motion.region_pairs[:, 0], motion.region_pairs[:, 1]],
        directed=True,
        config=context.polarity,
    )
    np.testing.assert_allclose(sampled.b_overrides_weight, expected)
    np.testing.assert_allclose(supplied.b_overrides_weight, expected)


def test_context_material_and_polarity_gradients_match_finite_differences():
    from src.worldgen.field.boundary_motion import BoundaryMotionGradientSample

    context, _, _, _, _, _ = _context(True)
    context = replace(
        context, polarity=PolarityConfig(preference_scale=4.0, seeded_bias=0.15)
    )
    position = np.array([[0.1, 0.0, 0.0]])
    motion = _motion_sample(
        [[0, 1]], convergence=[0.2], divergence=[0.1], influence=[0.8]
    )
    zeros = np.zeros((1, 3), dtype=np.float64)
    normal_jacobians = np.zeros((1, 3, 3), dtype=np.float64)
    motion_gradient = BoundaryMotionGradientSample(
        motion, zeros, zeros, zeros, zeros, zeros, zeros, normal_jacobians
    )
    analytic = context.sample_pairs_with_gradient(position, motion_gradient)
    step = 1e-6
    for field_name, gradient_name in (
        ("continental_blend", "continental_blend_gradients"),
        ("b_overrides_weight", "b_overrides_weight_gradients"),
    ):
        numerical = np.empty((1, 3))
        for axis in range(3):
            offset = np.zeros_like(position)
            offset[0, axis] = step
            positive = getattr(
                context.sample_pairs(position + offset, motion), field_name
            )[0]
            negative = getattr(
                context.sample_pairs(position - offset, motion), field_name
            )[0]
            numerical[0, axis] = (positive - negative) / (2.0 * step)
        np.testing.assert_allclose(
            getattr(analytic, gradient_name), numerical, rtol=2e-5, atol=2e-7
        )
