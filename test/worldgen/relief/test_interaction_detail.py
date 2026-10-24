from dataclasses import replace

import numpy as np


from src.worldgen.field.noise import NoiseConfig
from src.worldgen.relief.collision import collision_profile_with_partials
from src.worldgen.relief.fault import fault_profile_with_partials
from src.worldgen.relief.profile_config import ReliefProfileConfig
from src.worldgen.relief.ridge_detail import RidgeDetailConfig, RidgeDetailField
from src.worldgen.relief.subduction import subduction_profile_with_partials
from src.worldgen.relief.tectonic_response import (
    TectonicResponseConfig,
    blend_subduction_orientations,
    divergent_relief,
    shear_boundary_relief,
    transform_boundary_relief,
)
from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world_field


def test_arc_detail_preserves_trench_and_changes_overriding_arc():
    distance = np.array([-0.1, 0.0, 0.25])
    ones = np.ones(3)
    config = TectonicResponseConfig(
        subduction=ReliefProfileConfig(width_percent=100, height_percent=100),
        subduction_arc_height_multiplier=1.3,
        subduction_trench_depth_multiplier=0.7,
    )
    base = blend_subduction_orientations(
        distance,
        ones,
        ones,
        ones,
        config=config.subduction,
        arc_height_multiplier=config.subduction_arc_height_multiplier,
        trench_depth_multiplier=config.subduction_trench_depth_multiplier,
    )
    varied = blend_subduction_orientations(
        distance,
        ones,
        ones,
        ones,
        config=config.subduction,
        arc_height_multiplier=config.subduction_arc_height_multiplier,
        trench_depth_multiplier=config.subduction_trench_depth_multiplier,
        detail_weights=np.zeros(3),
        detail_strength=0.45,
    )
    np.testing.assert_array_equal(varied[:2], base[:2])
    assert 0 < varied[2] < base[2]
    reversed_pair = blend_subduction_orientations(
        -distance,
        ones,
        np.zeros(3),
        ones,
        config=config.subduction,
        arc_height_multiplier=config.subduction_arc_height_multiplier,
        trench_depth_multiplier=config.subduction_trench_depth_multiplier,
        detail_weights=np.zeros(3),
        detail_strength=0.45,
    )
    np.testing.assert_array_equal(varied, reversed_pair)


def test_divergent_detail_preserves_axes_and_varies_shoulders():
    distance = np.array([0.0, 0.06])
    ones = np.ones(2)
    for material in (np.zeros(2), ones):
        base = divergent_relief(distance, ones, ones, material)
        varied = divergent_relief(
            distance,
            ones,
            ones,
            material,
            detail_weights=np.zeros(2),
            ridge_detail_strength=0.3,
            rift_detail_strength=0.3,
        )
        assert varied[0] == base[0]
        assert varied[1] != base[1]
        gated = divergent_relief(
            distance,
            ones,
            np.zeros(2),
            material,
            detail_weights=ones,
            ridge_detail_strength=0.3,
            rift_detail_strength=0.3,
        )
        np.testing.assert_array_equal(gated, np.zeros(2))


def test_fault_detail_preserves_sign_and_support():
    distance = np.array([0.0, 0.0, 0.0, 1.0])
    closing = np.array([1.0, -1.0, 0.0, 1.0])
    ones = np.ones(4)
    for response in (transform_boundary_relief, shear_boundary_relief):
        base = response(
            distance, closing, ones, ones, smoothing=0.01, response_scale=1.0
        )
        varied = response(
            distance,
            closing,
            ones,
            ones,
            smoothing=0.01,
            response_scale=1.0,
            detail_weights=np.zeros(4),
            detail_strength=0.15,
        )
        np.testing.assert_allclose(varied, base * 0.85)
        np.testing.assert_array_equal(np.sign(varied), np.sign(base))
        assert varied[-1] == 0


def test_independent_relief_fields_match_combined_path_with_detail():
    world = generate_world_field(WorldgenConfig(seed=2026))
    points = np.random.default_rng(73).uniform(-1.2, 1.2, (1307, 3))
    sample = world.sample_world(points)
    for name in (
        "convergent_relief",
        "divergent_relief",
        "transform_relief",
        "shear_relief",
    ):
        np.testing.assert_allclose(
            getattr(world, name).sample(points),
            getattr(sample.elevation, name),
            atol=1e-15,
        )


def test_response_smoothing_changes_only_fault_relief_and_matches_independent_fields():
    config = WorldgenConfig(seed=2026)
    baseline = generate_world_field(config)
    smoothed = generate_world_field(
        replace(
            config,
            relief=replace(
                config.relief,
                tectonic=replace(config.relief.tectonic, motion_smoothing_width=0.25),
            ),
        )
    )
    points = np.random.default_rng(73).uniform(-1.2, 1.2, (1307, 3))
    before = baseline.sample_world(points)
    after = smoothed.sample_world(points)
    for name in before.geology.__dataclass_fields__:
        np.testing.assert_array_equal(
            getattr(before.geology, name), getattr(after.geology, name)
        )
    for name in (
        "coastal_elevation",
        "convergent_relief",
        "divergent_relief",
        "volcanic_relief",
        "terrain_variation",
    ):
        np.testing.assert_array_equal(
            getattr(before.elevation, name), getattr(after.elevation, name)
        )
    source_points = baseline.warp.sample(points)
    motion = baseline.geology.motion.sample(source_points)
    for kind in ("transform", "shear"):
        original_pairs = getattr(baseline.source_relief.sampler, f"sample_{kind}")(
            source_points, motion
        )
        modified_pairs = getattr(smoothed.source_relief.sampler, f"sample_{kind}")(
            source_points, motion
        )
        active = np.abs(original_pairs) > 1e-12
        assert np.any(active)
        assert np.all(np.abs(modified_pairs[active]) < np.abs(original_pairs[active]))
        np.testing.assert_array_equal(np.sign(modified_pairs), np.sign(original_pairs))
        # Signed transform contributions can cancel at junctions; their sum
        # need not decrease monotonically even when every pair is attenuated.
        name = f"{kind}_relief"
        original = getattr(before.elevation, name)
        modified = getattr(after.elevation, name)
        assert np.any(np.abs(modified - original) > 1e-12)
        np.testing.assert_allclose(
            getattr(smoothed, name).sample(points), modified, atol=1e-15
        )


def test_fault_profile_partials_cover_width_distance_and_compact_support():
    distance, width = 0.21, 0.8
    value, d_distance, d_width = fault_profile_with_partials(distance, width)
    epsilon = 1e-6
    np.testing.assert_allclose(
        d_distance,
        (
            fault_profile_with_partials(distance + epsilon, width)[0]
            - fault_profile_with_partials(distance - epsilon, width)[0]
        )
        / (2.0 * epsilon),
        rtol=1e-7,
    )
    np.testing.assert_allclose(
        d_width,
        (
            fault_profile_with_partials(distance, width + epsilon)[0]
            - fault_profile_with_partials(distance, width - epsilon)[0]
        )
        / (2.0 * epsilon),
        rtol=1e-7,
    )
    assert value > 0.0 and d_distance < 0.0
    assert fault_profile_with_partials(width, width) == (0.0, 0.0, 0.0)
    broad, crest, broad_d, crest_d = collision_profile_with_partials(
        distance, width, 0.3
    )
    assert broad > 0.0 and crest > 0.0 and broad_d < 0.0 and crest_d < 0.0
    assert collision_profile_with_partials(width, width, 0.3) == (
        0.0,
        0.0,
        0.0,
        0.0,
    )


def test_subduction_profile_partials_handle_arc_and_trench_channels():
    signed_distance, width = 0.25, 0.8
    values = subduction_profile_with_partials(signed_distance, width)
    epsilon = 1e-6
    d_distance = (
        subduction_profile_with_partials(signed_distance + epsilon, width)[0]
        - subduction_profile_with_partials(signed_distance - epsilon, width)[0]
    ) / (2.0 * epsilon)
    d_width = (
        subduction_profile_with_partials(signed_distance, width + epsilon)[0]
        - subduction_profile_with_partials(signed_distance, width - epsilon)[0]
    ) / (2.0 * epsilon)
    np.testing.assert_allclose(values[1], d_distance, rtol=1e-7)
    np.testing.assert_allclose(values[2], d_width, rtol=1e-7)
    assert values[3] > 0.0
    assert subduction_profile_with_partials(-0.1, width)[3] == 0.0


def test_ridge_detail_gradient_is_zero_at_clipped_noise_endpoints():
    field = RidgeDetailField(
        noise_seed=1729,
        config=replace(
            RidgeDetailConfig(),
            noise=NoiseConfig(octaves=1, base_frequency=0.0),
        ),
    )
    positions = np.array([[0.2, 0.3, 0.4], [-0.7, 0.1, 0.2]], dtype=np.float64)
    result = field.sample_with_gradient(positions)
    np.testing.assert_array_equal(result.values, field.sample(positions))
    np.testing.assert_array_equal(result.gradients, np.zeros((2, 3)))


def test_ridge_detail_gradient_tracks_spatial_noise_variation():
    field = RidgeDetailField(
        noise_seed=417,
        config=replace(
            RidgeDetailConfig(),
            noise=NoiseConfig(octaves=2, base_frequency=1.2),
        ),
    )
    positions = np.array([[0.31, -0.27, 0.19]], dtype=np.float64)
    sample = field.sample_with_gradient(positions)
    epsilon = 3e-3
    finite_difference = np.empty(3, dtype=np.float64)
    for axis in range(3):
        offset = np.zeros_like(positions)
        offset[0, axis] = epsilon
        finite_difference[axis] = (
            field.sample(positions + offset)[0] - field.sample(positions - offset)[0]
        ) / (2.0 * epsilon)
    assert np.linalg.norm(sample.gradients[0] - finite_difference) < (
        0.01 * np.linalg.norm(sample.gradients[0])
    )
