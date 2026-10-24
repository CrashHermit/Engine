from dataclasses import fields, replace

import numpy as np
import pytest
from numba import get_num_threads, set_num_threads

from src.worldgen.relief.variation import TerrainVariationConfig, TerrainVariationField
from src.worldgen.relief.coastal import SourceCoastalConfig, SourceCoastalSpanConfig
from src.worldgen.relief.profile_config import ReliefProfileConfig
from src.worldgen.relief.tectonic_response import (
    TectonicResponseConfig,
    TectonicResponseSampler,
    convergent_relief,
    divergent_relief,
    shear_boundary_relief,
    transform_boundary_relief,
)
from src.worldgen.relief.ridge_detail import RidgeDetailConfig
from src.worldgen.field.boundary_motion import BoundaryMotionField
from src.worldgen.field.boundary_response import BoundaryResponseField
from src.worldgen.field.boundary_vector import BoundaryVectorField
from src.worldgen.field.compose import SumScalarField, WarpedScalarField
from src.worldgen.field.differential import ScalarSample, VectorSample
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
from src.worldgen.relief.coastal import SourceCoastalField
from src.worldgen.relief.ridge_detail import RidgeDetailField


def test_motion_response_scale_changes_relief_without_changing_raw_fields():
    motion, context, sampler, _ = _continuous_tectonic_fixture()
    positions = np.array([[0.0, 0.0, 0.0], [0.2, 0.1, 0.0]])
    raw_motion = motion.sample(positions)
    raw_context = context.sample_pairs(positions, raw_motion)
    original = sampler.sample_from_context(raw_context)

    slower = TectonicResponseSampler(
        sampler.sample_context,
        replace(sampler.config, motion_response_scale=4.0),
        sample_context_with_gradient=sampler.sample_context_with_gradient,
    )
    scaled = slower.sample_from_context(raw_context)
    scaled_motion = motion.sample(positions)
    scaled_context = context.sample_pairs(positions, scaled_motion)

    np.testing.assert_array_equal(scaled_motion.convergence, raw_motion.convergence)
    np.testing.assert_array_equal(scaled_motion.divergence, raw_motion.divergence)
    np.testing.assert_array_equal(scaled_motion.shear, raw_motion.shear)
    np.testing.assert_array_equal(raw_context.convergence, scaled_context.convergence)
    np.testing.assert_array_equal(raw_context.divergence, scaled_context.divergence)
    np.testing.assert_array_equal(raw_context.shear, scaled_context.shear)
    np.testing.assert_array_equal(
        raw_context.plane_distance, scaled_context.plane_distance
    )
    np.testing.assert_array_equal(raw_context.influence, scaled_context.influence)
    assert not np.array_equal(original.total, scaled.total)


def test_source_relief_config_uses_radius_percentages():
    config = ReliefProfileConfig(width_percent=12.0, height_percent=0.5)

    assert config.width_fraction == 0.12
    assert config.height_fraction == 0.005


def test_convergent_relief_blends_collision_and_ordered_subduction():
    distance = np.array([-0.3, -0.08, 0.0, 0.04, 0.25])
    convergence = np.array([0.4, 0.8, 1.0, 0.6, 0.2])
    overriding = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    influence = np.array([1.0, 0.7, 0.5, 0.25, 0.0])
    continental = np.array([1.0, 0.8, 0.5, 0.2, 0.0])
    config = TectonicResponseConfig(
        collision=ReliefProfileConfig(width_percent=40.0, height_percent=170.0),
        subduction=ReliefProfileConfig(width_percent=30.0, height_percent=90.0),
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
        "collision": ReliefProfileConfig(height_percent=0.0),
        "subduction": ReliefProfileConfig(width_percent=100.0, height_percent=100.0),
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
        rift=ReliefProfileConfig(width_percent=45.0, height_percent=120.0),
        ridge=ReliefProfileConfig(width_percent=25.0, height_percent=70.0),
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


def test_fault_responses_apply_signed_saturating_amplitudes():
    distance = np.zeros(4)
    closing = np.array([0.0, 2.0, -2.0, 0.0])
    sliding = np.array([2.0, 2.0, 2.0, 0.0])
    influence = np.ones(4)
    unit_config = ReliefProfileConfig(width_percent=100.0, height_percent=100.0)

    transform = transform_boundary_relief(
        distance,
        closing,
        sliding,
        influence,
        config=unit_config,
        smoothing=0.01,
        response_scale=0.5,
    )
    pure_shear = shear_boundary_relief(
        distance,
        closing,
        sliding,
        influence,
        config=unit_config,
        smoothing=0.01,
        response_scale=0.5,
    )

    np.testing.assert_array_equal(np.sign(transform), [0.0, 1.0, -1.0, 0.0])
    assert pure_shear[0] > 0.0
    assert pure_shear[-1] == 0.0
    assert np.all(pure_shear >= 0.0)
    assert np.all(np.abs(transform) < 1.0)
    np.testing.assert_allclose(
        transform_boundary_relief(
            distance,
            -closing,
            sliding,
            influence,
            config=unit_config,
            smoothing=0.01,
            response_scale=0.5,
        ),
        -transform,
    )
    np.testing.assert_allclose(
        shear_boundary_relief(
            distance,
            -closing,
            sliding,
            influence,
            config=unit_config,
            smoothing=0.01,
            response_scale=0.5,
        ),
        pure_shear,
    )

    np.testing.assert_array_equal(
        transform_boundary_relief(
            distance,
            np.ones(4),
            np.zeros(4),
            influence,
            config=unit_config,
            smoothing=0.01,
            response_scale=0.5,
        ),
        np.zeros(4),
    )
    np.testing.assert_array_equal(
        shear_boundary_relief(
            distance,
            np.ones(4),
            np.zeros(4),
            influence,
            config=unit_config,
            smoothing=0.01,
            response_scale=0.5,
        ),
        np.zeros(4),
    )
    at_and_beyond_support = transform_boundary_relief(
        np.array([0.0, 1.0, 1.5]),
        np.ones(3),
        np.ones(3),
        np.ones(3),
        config=unit_config,
        smoothing=0.01,
        response_scale=0.5,
    )
    np.testing.assert_array_equal(at_and_beyond_support[-2:], [0.0, 0.0])
    np.testing.assert_array_equal(
        transform_boundary_relief(
            -distance,
            closing,
            sliding,
            influence,
            config=unit_config,
            smoothing=0.01,
            response_scale=0.5,
        ),
        transform,
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
    unit_relief = ReliefProfileConfig(width_percent=100.0, height_percent=100.0)
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
    relief = sampler.sample_from_context(context_sample)
    source_values = source.sample(positions)

    np.testing.assert_allclose(context_sample.convergence, [1.0])
    assert 0.99 < context_sample.shear[0] < 1.0
    assert relief.transform[0] > 0.0
    assert relief.shear[0] > 0.0
    assert source_values[0] > 0.0
    assert source_values[1] == 0.0
    assert source.sample(np.empty((0, 3))).shape == (0,)

    coast = SourceCoastalField(
        sample_continental_weight=lambda points: np.full(len(points), 0.2),
        sample_density_anomaly=lambda points: np.zeros(len(points)),
        influence_span_noise_seeds=(1, 2, 3),
        sample_continental_weight_with_gradient=lambda points: ScalarSample(
            np.full(len(points), 0.2), np.zeros((len(points), 3))
        ),
        sample_density_anomaly_with_gradient=lambda points: ScalarSample(
            np.zeros(len(points)), np.zeros((len(points), 3))
        ),
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
    unit_relief = ReliefProfileConfig(width_percent=100.0, height_percent=100.0)
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
        sample_material_gradient=material.sample_with_gradient,
        sample_preference_jacobian=preference.sample_with_jacobian,
    )
    context_sample = context.sample_pairs(query, motion_sample)
    sampler = TectonicResponseSampler(
        context.sample_pairs,
        config,
        sample_context_with_gradient=context.sample_pairs_with_gradient,
    )
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
    slopes = (
        (1.0, 0.0, 0.0),
        (0.0, 0.0, 0.1),
        (0.04, 0.0, 0.0),
        (0.0, 0.05, 0.0),
        (0.02, 0.0, 0.0),
        (0.0, 0.0, 0.03),
        (0.0, 0.2, 0.0),
    )

    def context_with_gradient(query, motion):
        return TectonicContextGradientSample(
            context(query), *(np.tile(slope, (len(query), 1)) for slope in slopes)
        )

    gradients = context_with_gradient(points, None)
    sampler = TectonicResponseSampler(
        lambda p, motion: context(p),
        sample_context_with_gradient=context_with_gradient,
    )
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


def test_tectonic_response_gradients_include_saturation_chain_for_large_motion():
    def context(points):
        return TectonicContextSample(
            plane_distance=0.05 + 0.02 * points[:, 0],
            continental_blend=0.6 + 0.01 * points[:, 2],
            b_overrides_weight=0.4 + 0.01 * points[:, 0],
            convergence=12.0 + 0.3 * points[:, 1],
            divergence=5.0 + 0.2 * points[:, 0],
            shear=8.0 + 0.1 * points[:, 2],
            influence=0.55 + 0.1 * points[:, 1],
        )

    point = np.array([[0.03, 0.04, -0.02]])
    slopes = (
        (0.02, 0.0, 0.0),
        (0.0, 0.0, 0.01),
        (0.01, 0.0, 0.0),
        (0.0, 0.3, 0.0),
        (0.2, 0.0, 0.0),
        (0.0, 0.0, 0.1),
        (0.0, 0.1, 0.0),
    )

    def context_with_gradient(points, motion):
        return TectonicContextGradientSample(
            context(points), *(np.tile(slope, (len(points), 1)) for slope in slopes)
        )

    gradients = context_with_gradient(point, None)
    unit = ReliefProfileConfig(width_percent=100.0, height_percent=100.0)
    sampler = TectonicResponseSampler(
        lambda positions, motion: context(positions),
        TectonicResponseConfig(
            collision=unit,
            subduction=unit,
            rift=unit,
            ridge=unit,
            transform=unit,
            shear=unit,
            motion_response_scale=2.0,
        ),
        sample_context_with_gradient=context_with_gradient,
    )
    result = sampler.sample_from_context_with_gradient(gradients)

    step = 1e-6
    for channel in ("convergent", "divergent", "transform", "shear", "total"):
        numerical = np.empty((1, 3))
        for axis in range(3):
            offset = np.zeros_like(point)
            offset[0, axis] = step
            positive = getattr(
                sampler.sample_from_context(context(point + offset)), channel
            )[0]
            negative = getattr(
                sampler.sample_from_context(context(point - offset)), channel
            )[0]
            numerical[0, axis] = (positive - negative) / (2.0 * step)
        np.testing.assert_allclose(
            getattr(result, channel).gradients,
            numerical,
            rtol=3e-4,
            atol=1e-7,
        )


@pytest.mark.parametrize("detail_mode", ["absent", "enabled", "disabled"])
def test_response_gradients_preserve_chain_rules_and_parallel_record_order(detail_mode):
    def context(points):
        return TectonicContextSample(
            plane_distance=points[:, 0],
            continental_blend=0.5 + 0.2 * points[:, 1],
            b_overrides_weight=0.5 + 0.3 * points[:, 2],
            convergence=0.7 + 0.1 * points[:, 1],
            divergence=0.4 + 0.2 * points[:, 0],
            shear=0.5 + 0.1 * points[:, 2],
            influence=0.6 + 0.2 * points[:, 1],
        )

    def context_gradient(points):
        slopes = (
            (1.0, 0.0, 0.0),
            (0.0, 0.2, 0.0),
            (0.0, 0.0, 0.3),
            (0.0, 0.1, 0.0),
            (0.2, 0.0, 0.0),
            (0.0, 0.0, 0.1),
            (0.0, 0.2, 0.0),
        )
        return TectonicContextGradientSample(
            context(points), *(np.tile(slope, (len(points), 1)) for slope in slopes)
        )

    def ridge(points):
        if detail_mode == "absent":
            return None
        slope = np.array([0.1, 0.2, -0.15])
        return ScalarSample(
            0.5 + points @ slope,
            np.tile(slope, (len(points), 1)),
        )

    detail = None
    if detail_mode != "absent":
        config = RidgeDetailConfig()
        if detail_mode == "disabled":
            config = replace(
                config,
                blend=0.0,
                arc_strength=0.0,
                ridge_strength=0.0,
                rift_strength=0.0,
                transform_strength=0.0,
                shear_strength=0.0,
            )
        detail = RidgeDetailField(13, config)
    sampler = TectonicResponseSampler(
        lambda p, motion: context(p),
        ridge_detail=detail,
        sample_context_with_gradient=lambda points, motion: context_gradient(points),
    )
    points = np.random.default_rng(7314).uniform(-0.25, 0.25, (2062, 3))[::2]
    points.setflags(write=False)
    inputs = context_gradient(points)
    for item in fields(inputs.sample):
        getattr(inputs.sample, item.name).setflags(write=False)
    before = {
        item.name: getattr(inputs.sample, item.name).copy()
        for item in fields(inputs.sample)
    }
    ridge_sample = ridge(points)
    actual = sampler.sample_from_context_with_gradient(
        inputs, ridge_weights=ridge_sample
    )
    values = sampler.sample_from_context(
        inputs.sample,
        ridge_weights=None if ridge_sample is None else ridge_sample.values,
    )
    channels = ("convergent", "divergent", "transform", "shear", "total")
    step = 1e-6
    for axis in range(3):
        offset = np.eye(3)[axis] * step
        positive_points = points + offset
        negative_points = points - offset
        positive_ridge = ridge(positive_points)
        negative_ridge = ridge(negative_points)
        positive = sampler.sample_from_context(
            context(positive_points),
            ridge_weights=None if positive_ridge is None else positive_ridge.values,
        )
        negative = sampler.sample_from_context(
            context(negative_points),
            ridge_weights=None if negative_ridge is None else negative_ridge.values,
        )
        for channel in channels:
            numerical = (getattr(positive, channel) - getattr(negative, channel)) / (
                2.0 * step
            )
            np.testing.assert_allclose(
                getattr(actual, channel).gradients[:, axis],
                numerical,
                rtol=2e-4,
                atol=1e-9,
            )

    parts = [
        sampler.sample_from_context_with_gradient(
            context_gradient(points[start : start + 127]),
            ridge_weights=ridge(points[start : start + 127]),
        )
        for start in range(0, len(points), 127)
    ]
    original_threads = get_num_threads()
    try:
        for count in sorted({1, min(4, original_threads)}):
            set_num_threads(count)
            result = sampler.sample_from_context_with_gradient(
                inputs, ridge_weights=ridge_sample
            )
            for channel in channels:
                sample = getattr(result, channel)
                np.testing.assert_array_equal(sample.values, getattr(values, channel))
                np.testing.assert_array_equal(
                    sample.gradients,
                    np.concatenate(
                        [getattr(part, channel).gradients for part in parts]
                    ),
                )
                assert not sample.values.flags.writeable
                assert not sample.gradients.flags.writeable
    finally:
        set_num_threads(original_threads)

    empty = sampler.sample_from_context_with_gradient(
        context_gradient(points[:0]), ridge_weights=ridge(points[:0])
    )
    for channel in channels:
        sample = getattr(empty, channel)
        assert sample.values.shape == (0,)
        assert sample.gradients.shape == (0, 3)
        assert sample.gradients.dtype == np.float64
        assert not sample.gradients.flags.writeable
    for item in fields(inputs.sample):
        np.testing.assert_array_equal(
            getattr(inputs.sample, item.name), before[item.name]
        )
