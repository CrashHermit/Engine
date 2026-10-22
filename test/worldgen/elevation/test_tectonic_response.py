import numpy as np

from src.worldgen.elevation.variation import TerrainVariationField
from src.worldgen.elevation.config import (
    SourceCoastalConfig,
    SourceCoastalSpanConfig,
    SourceReliefConfig,
    TerrainVariationConfig,
    TectonicResponseConfig,
)
from src.worldgen.elevation.tectonic_response import (
    TectonicResponseSampler,
    convergent_relief,
    divergent_relief,
    shear_boundary_relief,
    transform_boundary_relief,
)
from src.worldgen.field.boundary_motion import BoundaryMotionField
from src.worldgen.field.boundary_response import BoundaryResponseField
from src.worldgen.field.boundary_vector import BoundaryVectorField
from src.worldgen.field.compose import SumScalarField, WarpedScalarField
from src.worldgen.field.differential import VectorSample
from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.region_overlap import RegionOverlapField
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField
from src.worldgen.geology.crust_field import CrustField
from src.worldgen.geology.crust_influence import CrustInfluenceField
from src.worldgen.geology.subduction_preference import SubductionPreferenceField
from src.worldgen.geology.tectonic_context import (
    TectonicContextField,
    TectonicContextGradientSample,
    TectonicContextSample,
)
from src.worldgen.elevation.source_coastal import SourceCoastalField


def test_source_relief_config_uses_radius_percentages():
    config = SourceReliefConfig(width_percent=12.0, height_percent=0.5)

    assert config.width_fraction == 0.12
    assert config.height_fraction == 0.005


def test_convergent_relief_blends_collision_and_ordered_subduction():
    distance = np.array([-0.3, -0.08, 0.0, 0.04, 0.25])
    convergence = np.array([0.4, 0.8, 1.0, 0.6, 0.2])
    overriding = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    influence = np.array([1.0, 0.7, 0.5, 0.25, 0.0])
    continental = np.array([1.0, 0.8, 0.5, 0.2, 0.0])
    config = TectonicResponseConfig(
        collision=SourceReliefConfig(width_percent=40.0, height_percent=170.0),
        subduction=SourceReliefConfig(width_percent=30.0, height_percent=90.0),
    )

    actual = convergent_relief(
        distance,
        convergence,
        overriding,
        influence,
        continental,
        config=config,
    )

    reversed_sides = convergent_relief(
        -distance,
        convergence,
        1.0 - overriding,
        influence,
        continental,
        config=config,
    )
    np.testing.assert_allclose(reversed_sides, actual, atol=1e-14)


def test_subduction_trench_depth_setting_scales_trench_not_arc():
    distance = np.array([0.0, 0.25])
    strength = np.ones(2)
    overriding = np.ones(2)
    influence = np.ones(2)
    oceanic = np.zeros(2)
    common = {
        "collision": SourceReliefConfig(height_percent=0.0),
        "subduction": SourceReliefConfig(width_percent=100.0, height_percent=100.0),
        "subduction_arc_height_multiplier": 1.5,
    }
    full_depth = convergent_relief(
        distance,
        strength,
        overriding,
        influence,
        oceanic,
        config=TectonicResponseConfig(**common, subduction_trench_depth_multiplier=1.0),
    )
    half_depth = convergent_relief(
        distance,
        strength,
        overriding,
        influence,
        oceanic,
        config=TectonicResponseConfig(**common, subduction_trench_depth_multiplier=0.5),
    )

    assert half_depth[0] == full_depth[0] * 0.5
    assert half_depth[1] == full_depth[1] > 0.0


def test_divergent_relief_blends_configured_rift_and_ridge_once():
    distance = np.array([-0.3, -0.08, 0.0, 0.04, 0.25])
    divergence = np.array([0.4, 0.8, 1.0, 0.6, 0.2])
    influence = np.array([1.0, 0.7, 0.5, 0.25, 0.0])
    continental = np.array([1.0, 0.8, 0.5, 0.2, 0.0])
    config = TectonicResponseConfig(
        rift=SourceReliefConfig(width_percent=45.0, height_percent=120.0),
        ridge=SourceReliefConfig(width_percent=25.0, height_percent=70.0),
    )
    actual = divergent_relief(
        distance, divergence, influence, continental, config=config
    )
    np.testing.assert_array_equal(actual[-1], 0.0)
    np.testing.assert_array_equal(
        divergent_relief(distance, divergence, np.zeros(5), continental, config=config),
        np.zeros(5),
    )
    np.testing.assert_array_equal(
        divergent_relief(distance, np.zeros(5), influence, continental, config=config),
        np.zeros(5),
    )
    np.testing.assert_allclose(
        divergent_relief(-distance, divergence, influence, continental, config=config),
        actual,
    )


def test_fault_responses_preserve_motion_sign_budget_and_compact_support():
    distance = np.zeros(4)
    closing = np.array([0.0, 2.0, -2.0, 0.0])
    sliding = np.array([2.0, 2.0, 2.0, 0.0])
    influence = np.ones(4)
    unit_config = SourceReliefConfig(width_percent=100.0, height_percent=100.0)

    transform = transform_boundary_relief(
        distance, closing, sliding, influence, config=unit_config, smoothing=0.01
    )
    pure_shear = shear_boundary_relief(
        distance, closing, sliding, influence, config=unit_config, smoothing=0.01
    )

    np.testing.assert_array_equal(np.sign(transform), [0.0, 1.0, -1.0, 0.0])
    assert pure_shear[0] > 0.0
    assert pure_shear[-1] == 0.0
    assert np.all(pure_shear >= 0.0)
    assert np.all(np.abs(transform) + pure_shear <= sliding)
    np.testing.assert_allclose(
        transform_boundary_relief(
            distance, -closing, sliding, influence, config=unit_config, smoothing=0.01
        ),
        -transform,
    )
    np.testing.assert_array_equal(
        shear_boundary_relief(
            distance, -closing, sliding, influence, config=unit_config, smoothing=0.01
        ),
        pure_shear,
    )

    zero_shear_transform = transform_boundary_relief(
        distance, np.ones(4), np.zeros(4), influence, config=unit_config, smoothing=0.01
    )
    zero_shear_profile = shear_boundary_relief(
        distance, np.ones(4), np.zeros(4), influence, config=unit_config, smoothing=0.01
    )
    np.testing.assert_array_equal(zero_shear_transform, np.zeros(4))
    np.testing.assert_array_equal(zero_shear_profile, np.zeros(4))

    half_influence = transform_boundary_relief(
        distance, closing, sliding, np.full(4, 0.5), config=unit_config, smoothing=0.01
    )
    np.testing.assert_allclose(half_influence, transform * 0.5)
    at_and_beyond_support = transform_boundary_relief(
        np.array([0.0, 1.0, 1.5]),
        np.ones(3),
        np.ones(3),
        np.ones(3),
        config=unit_config,
        smoothing=0.01,
    )
    np.testing.assert_array_equal(at_and_beyond_support[-2:], [0.0, 0.0])
    np.testing.assert_array_equal(
        transform_boundary_relief(
            -distance, closing, sliding, influence, config=unit_config, smoothing=0.01
        ),
        transform,
    )

    transform_config = TectonicResponseConfig(
        transform=SourceReliefConfig(width_percent=50.0, height_percent=25.0),
        shear=SourceReliefConfig(width_percent=100.0, height_percent=100.0),
    )
    shear_config = TectonicResponseConfig(
        transform=SourceReliefConfig(width_percent=100.0, height_percent=100.0),
        shear=SourceReliefConfig(width_percent=50.0, height_percent=25.0),
    )
    np.testing.assert_array_equal(
        transform_boundary_relief(
            distance,
            closing,
            sliding,
            influence,
            config=transform_config.transform,
            smoothing=0.01,
        ),
        0.25 * transform,
    )
    np.testing.assert_array_equal(
        shear_boundary_relief(
            distance,
            closing,
            sliding,
            influence,
            config=shear_config.shear,
            smoothing=0.01,
        ),
        0.25 * pure_shear,
    )


def _continuous_tectonic_fixture():
    seeds = np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    partition = VoronoiField3D(seeds)
    regions = RegionInfluenceField(partition, RegionInfluenceConfig(1.0))
    crust = CrustField(partition, np.array([True, True]))
    material = CrustInfluenceField(crust, regions)
    preference = SubductionPreferenceField(crust, regions)
    overlap = RegionOverlapField(regions)
    velocities = np.array([[0.0, 0.0, 0.0], [-1.0, 1.0, 0.0]])
    motion = BoundaryMotionField(
        BoundaryVectorField(
            overlap,
            lambda positions, ids: velocities[ids],
            lambda positions, ids: VectorSample(
                velocities[ids], np.zeros((len(ids), 3, 3), dtype=np.float64)
            ),
        )
    )
    context = TectonicContextField(
        material.sample,
        preference.sample,
        np.array([[0.0, 1.0], [-1.0, 0.0]]),
        directed=False,
        sample_material_gradient=material.sample_with_gradient,
        sample_preference_jacobian=preference.sample_with_jacobian,
    )
    unit_relief = SourceReliefConfig(width_percent=100.0, height_percent=100.0)
    config = TectonicResponseConfig(
        collision=unit_relief,
        subduction=unit_relief,
        rift=unit_relief,
        ridge=unit_relief,
        transform=unit_relief,
        shear=unit_relief,
    )
    sampler = TectonicResponseSampler(
        context.sample_pairs,
        config,
        sample_context_with_gradient=context.sample_pairs_with_gradient,
    )

    def response(positions, motion_sample):
        if len(motion_sample.query_indices) == 0:
            return np.empty(0)
        context_sample = context.sample_pairs(positions, motion_sample)
        return sampler.sample_from_context(context_sample).total

    source = BoundaryResponseField(motion, response)
    return motion, context, sampler, source


def test_sampler_composes_real_continuous_fault_fields_and_coast():
    motion, context, sampler, source = _continuous_tectonic_fixture()
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    sample = motion.sample(positions)
    context_sample = context.sample_pairs(positions, sample)

    np.testing.assert_allclose(context_sample.convergence, [1.0])
    assert 0.99 < context_sample.shear[0] < 1.0
    relief = sampler.sample_from_context(context_sample)
    assert 0.0 < relief.transform[0] < 0.5
    assert 0.0 < relief.shear[0] < 0.5
    source_values = source.sample(positions)
    assert 3.0 < source_values[0] < 4.0
    assert source_values[1] == 0.0
    assert source.sample(np.empty((0, 3))).shape == (0,)

    coast = SourceCoastalField(
        sample_continental_weight=lambda points: np.full(len(points), 0.2),
        sample_density_anomaly=lambda points: np.zeros(len(points)),
        span_noise_seeds=(1, 2, 3),
        config=SourceCoastalConfig(
            coastline_weight=0.54,
            inland=SourceCoastalSpanConfig(0.06, 0.0),
            shelf=SourceCoastalSpanConfig(0.04, 0.0),
            slope=SourceCoastalSpanConfig(0.04, 0.0),
        ),
    )
    warp = ShearWarpField(
        ShearWarpConfig(iterations=1, amplitude=1.0),
        lambda plane, iteration, axis, frequency: (
            plane[:, 0] if axis == 0 else np.zeros(len(plane))
        ),
    )
    elevation_source = lambda points: (
        coast.sample_elevation(points) + source.sample(points)
    )
    world = WarpedScalarField(warp.sample, elevation_source)
    world_point = np.array([[-1.0, 1.0, 0.0]])
    source_point = warp.sample(world_point)
    np.testing.assert_array_equal(source_point, [[0.0, 1.0, 0.0]])
    np.testing.assert_allclose(
        world.sample(world_point), elevation_source(source_point)
    )

    variation = TerrainVariationField(
        TerrainVariationConfig(amplitude_percent=0.004), 17
    )
    completed = SumScalarField((world.sample, variation.sample_fraction))
    query = np.array([[-1.0, 1.0, 0.2], [0.1, 0.5, -0.4], [0.7, -0.2, 0.3]])
    unwarped_noise = variation.sample_fraction(query)
    np.testing.assert_allclose(
        completed.sample(query) - world.sample(query), unwarped_noise, atol=1e-16
    )
    assert not np.allclose(
        unwarped_noise, variation.sample_fraction(warp.sample(query))
    )
    assert not completed.sample(query).flags.writeable
    assert completed.sample(np.empty((0, 3))).shape == (0,)


def test_tectonic_response_gradient_matches_source_space_composition():
    motion, context, sampler, _ = _continuous_tectonic_fixture()
    position = np.array([[0.13, 0.17, 0.11]], dtype=np.float64)
    motion_gradient = motion.sample_with_gradient(position)
    context_gradient = context.sample_pairs_with_gradient(position, motion_gradient)
    result = sampler.sample_from_context_with_gradient(context_gradient)
    epsilon = 1e-6
    for channel in ("convergent", "divergent", "transform", "shear", "total"):
        finite_difference = np.empty(3, dtype=np.float64)
        for axis in range(3):
            offset = np.zeros_like(position)
            offset[0, axis] = epsilon
            positive = position + offset
            negative = position - offset
            positive_motion = motion.sample(positive)
            negative_motion = motion.sample(negative)
            positive_value = getattr(
                sampler.sample_from_context(
                    context.sample_pairs(positive, positive_motion)
                ),
                channel,
            )
            negative_value = getattr(
                sampler.sample_from_context(
                    context.sample_pairs(negative, negative_motion)
                ),
                channel,
            )
            finite_difference[axis] = (positive_value[0] - negative_value[0]) / (
                2.0 * epsilon
            )
        np.testing.assert_allclose(
            getattr(result, channel).gradients[0],
            finite_difference,
            rtol=2e-4,
            atol=1e-6,
        )


def test_fault_relief_includes_non_face_overlaps_and_junction_contributions():
    seeds = np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0]])
    partition = VoronoiField3D(seeds)
    regions = RegionInfluenceField(partition, RegionInfluenceConfig(0.5))
    overlap = RegionOverlapField(regions)
    crust = CrustField(partition, np.ones(3, dtype=bool))
    material = CrustInfluenceField(crust, regions)
    preference = SubductionPreferenceField(crust, regions)
    velocities = np.array([[0.0, 0.0, 0.0], [-1.0, 1.0, 0.0], [0.0, 0.0, 0.0]])
    query = np.array([[0.0, 0.75, 0.0]])
    unit_relief = SourceReliefConfig(width_percent=100.0, height_percent=100.0)
    config = TectonicResponseConfig(
        collision=unit_relief,
        subduction=unit_relief,
        rift=unit_relief,
        ridge=unit_relief,
        transform=unit_relief,
        shear=unit_relief,
    )
    motion = BoundaryMotionField(
        BoundaryVectorField(overlap, lambda positions, ids: velocities[ids])
    )
    motion_sample = motion.sample(query)
    np.testing.assert_array_equal(
        motion_sample.region_pairs,
        np.array([[0, 1], [0, 2], [1, 2]], dtype=np.int64),
    )
    np.testing.assert_allclose(motion_sample.influence, np.full(3, 4.0 / 9.0))
    context = TectonicContextField(
        material.sample,
        preference.sample,
        np.array([[0, 1, 1], [-1, 0, 1], [-1, -1, 0]], dtype=np.float64),
        directed=False,
    )
    context_sample = context.sample_pairs(query, motion_sample)
    sampler = TectonicResponseSampler(context.sample_pairs, config)
    response = sampler.sample_from_context(context_sample)
    assert np.all(np.abs(response.total) <= 4.0)
    assert np.any(response.total != 0.0)


def test_relief_gradients_include_varying_overlap_material_and_polarity():
    def context(points):
        return TectonicContextSample(
            plane_distance=points[:, 0],
            continental_blend=0.5 + 0.1 * points[:, 2],
            b_overrides_weight=0.35 + 0.04 * points[:, 0],
            convergence=0.7 + 0.05 * points[:, 1],
            divergence=0.2 + 0.02 * points[:, 0],
            shear=0.4 + 0.03 * points[:, 2],
            influence=0.3 + 0.2 * points[:, 1],
        )

    points = np.array([[0.04, 0.1, -0.2], [-0.06, -0.2, 0.3]])
    gradients = TectonicContextGradientSample(
        sample=context(points),
        plane_distance_gradients=np.tile([1.0, 0.0, 0.0], (2, 1)),
        continental_blend_gradients=np.tile([0.0, 0.0, 0.1], (2, 1)),
        b_overrides_weight_gradients=np.tile([0.04, 0.0, 0.0], (2, 1)),
        convergence_gradients=np.tile([0.0, 0.05, 0.0], (2, 1)),
        divergence_gradients=np.tile([0.02, 0.0, 0.0], (2, 1)),
        shear_gradients=np.tile([0.0, 0.0, 0.03], (2, 1)),
        influence_gradients=np.tile([0.0, 0.2, 0.0], (2, 1)),
    )
    sampler = TectonicResponseSampler(lambda p, motion: context(p))
    actual = sampler.sample_from_context_with_gradient(gradients)
    step = 1e-6
    for channel in ("convergent", "divergent", "transform", "shear", "total"):
        numerical = np.column_stack(
            [
                (
                    getattr(
                        sampler.sample_from_context(
                            context(points + np.eye(3)[axis] * step)
                        ),
                        channel,
                    )
                    - getattr(
                        sampler.sample_from_context(
                            context(points - np.eye(3)[axis] * step)
                        ),
                        channel,
                    )
                )
                / (2 * step)
                for axis in range(3)
            ]
        )
        np.testing.assert_allclose(
            getattr(actual, channel).gradients, numerical, rtol=1e-6, atol=1e-9
        )
