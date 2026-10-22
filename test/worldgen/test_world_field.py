from dataclasses import replace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world_field
from src.worldgen.geometry.differential import (
    pushforward_normals,
    pushforward_vectors,
)


def _positions() -> np.ndarray:
    random = np.random.default_rng(90210)
    return np.vstack(
        (
            np.array([[0.0, 0.0, 0.0], [1.7, -0.2, 0.3], [-0.4, 0.8, 1.2]]),
            random.uniform(-1.5, 1.5, size=(257, 3)),
        )
    )


def _assert_arrays_equal(left, right) -> None:
    for name in left.__dataclass_fields__:
        first = getattr(left, name)
        second = getattr(right, name)
        if isinstance(first, np.ndarray):
            np.testing.assert_array_equal(first, second)
        else:
            _assert_arrays_equal(first, second)


def test_world_sampling_uses_source_warp_and_original_world_variation_coordinates():
    field = generate_world_field(WorldgenConfig(seed=2026))
    positions = _positions()
    untouched = positions.copy()

    sample = field.sample_world(positions)
    source = field.warp.sample(positions)
    source_elevation = field.source_elevation.sample_total_source(source)
    variation = field.variation.sample_fraction(positions)

    np.testing.assert_array_equal(positions, untouched)
    np.testing.assert_allclose(
        sample.elevation.elevation, field.elevation.sample(positions)
    )
    np.testing.assert_allclose(
        sample.elevation.elevation,
        source_elevation + variation,
        rtol=1e-13,
        atol=1e-13,
    )
    assert np.any(np.abs(variation - field.variation.sample_fraction(source)) > 1e-10)
    assert not sample.elevation.elevation.flags.writeable


def test_zero_variation_preserves_geology_and_source_relief_without_gating():
    config = WorldgenConfig(seed=123)
    enabled = generate_world_field(config)
    disabled = generate_world_field(
        replace(
            config,
            elevation=replace(
                config.elevation,
                variation=replace(config.elevation.variation, amplitude_percent=0.0),
            ),
        )
    )
    positions = _positions()
    active = enabled.sample_world(positions)
    flat = disabled.sample_world(positions)

    _assert_arrays_equal(active.geology, flat.geology)
    for name in active.elevation.__dataclass_fields__:
        if name in ("terrain_variation", "elevation"):
            continue
        np.testing.assert_array_equal(
            getattr(active.elevation, name), getattr(flat.elevation, name)
        )
    expected_variation = enabled.variation.sample_fraction(positions)
    np.testing.assert_allclose(
        active.elevation.elevation - flat.elevation.elevation,
        expected_variation,
        rtol=1e-13,
        atol=1e-13,
    )
    np.testing.assert_array_equal(
        flat.elevation.terrain_variation, np.zeros(len(positions))
    )

    source = enabled.warp.sample(positions)
    geology = enabled.geology.sample_source(source).result
    assert np.any(geology.continental_mask)
    assert np.any(~geology.continental_mask)
    assert np.any(geology.region_overlap == 0.0)
    np.testing.assert_array_equal(
        expected_variation[geology.region_overlap == 0.0],
        enabled.variation.sample_fraction(positions)[geology.region_overlap == 0.0],
    )
    assert np.any(expected_variation[geology.region_overlap == 0.0] != 0.0)


def test_world_queries_are_partition_order_empty_and_immutable():
    field = generate_world_field(WorldgenConfig(seed=31415))
    positions = _positions()
    original = positions.copy()
    whole = field.sample_world(positions)
    split = field.sample_world(positions[:91])
    remainder = field.sample_world(positions[91:])
    order = np.random.default_rng(7).permutation(len(positions))
    reordered = field.sample_world(positions[order])
    empty = field.sample_world(np.empty((0, 3), dtype=np.float64))

    np.testing.assert_array_equal(positions, original)
    _assert_arrays_equal(
        split.geology,
        type(whole.geology)(
            **{
                name: getattr(whole.geology, name)[:91]
                for name in whole.geology.__dataclass_fields__
            }
        ),
    )
    for result, reordered_result in (
        (whole.geology, reordered.geology),
        (whole.elevation, reordered.elevation),
    ):
        for name in result.__dataclass_fields__:
            value = getattr(result, name)
            np.testing.assert_array_equal(value[order], getattr(reordered_result, name))
            assert not value.flags.writeable
    for result in (empty.geology, empty.elevation):
        for name in result.__dataclass_fields__:
            value = getattr(result, name)
            assert value.shape == (0,)
            assert value.dtype in (
                np.dtype(np.float64),
                np.dtype(np.int64),
                np.dtype(bool),
            )
            assert not value.flags.writeable
    np.testing.assert_allclose(
        np.concatenate((split.elevation.elevation, remainder.elevation.elevation)),
        whole.elevation.elevation,
        rtol=1e-13,
        atol=1e-13,
    )


def test_seeded_world_field_is_reproducible_and_does_not_use_global_rng():
    config = WorldgenConfig(seed=2026)
    positions = _positions()
    np.random.seed(37)
    before = np.random.get_state()
    first = generate_world_field(config)
    sample = first.sample_world(positions)
    after = np.random.get_state()
    repeat = generate_world_field(config)
    repeated_sample = repeat.sample_world(positions)
    other = generate_world_field(replace(config, seed=config.seed + 1))

    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]
    _assert_arrays_equal(sample.geology, repeated_sample.geology)
    _assert_arrays_equal(sample.elevation, repeated_sample.elevation)
    np.testing.assert_array_equal(
        first.geology.regions.voronoi.seeds,
        repeat.geology.regions.voronoi.seeds,
    )
    assert not np.array_equal(
        first.geology.regions.voronoi.seeds,
        other.geology.regions.voronoi.seeds,
    )
    assert not np.array_equal(
        sample.geology.plate_ids, other.sample_world(positions).geology.plate_ids
    )


def test_world_elevation_gradient_matches_xyz_queries_and_radius_scaling():
    config = WorldgenConfig(seed=2026)
    # Keep noise well resolved for the full-chain diagnostic. Multi-octave
    # gradients are checked separately with float32-aware step sizes.
    config = replace(
        config,
        warp_noise=replace(config.warp_noise, octaves=1),
        elevation=replace(
            config.elevation,
            ridge_detail=replace(
                config.elevation.ridge_detail,
                noise=replace(config.elevation.ridge_detail.noise, octaves=1),
            ),
            variation=replace(
                config.elevation.variation,
                noise=replace(config.elevation.variation.noise, octaves=1),
            ),
        ),
    )
    field = generate_world_field(config)
    points = np.random.default_rng(31).uniform(-0.8, 0.8, (12, 3))
    sample = field.elevation.sample_with_gradient(points)
    step = 3e-4
    numerical = np.column_stack(
        [
            (
                field.elevation.sample(points + np.eye(3)[axis] * step)
                - field.elevation.sample(points - np.eye(3)[axis] * step)
            )
            / (2 * step)
            for axis in range(3)
        ]
    )
    np.testing.assert_allclose(
        sample.values, field.elevation.sample(points), rtol=1e-12, atol=1e-14
    )
    assert np.linalg.norm(sample.gradients - numerical) < 0.01 * np.linalg.norm(
        sample.gradients
    )
    meters = field.sample_elevation_meters_with_gradient(points, radius_m=6_371_000.0)
    larger = field.sample_elevation_meters_with_gradient(points, radius_m=12_742_000.0)
    np.testing.assert_array_equal(larger.values, 2 * meters.values)
    np.testing.assert_array_equal(larger.gradients, 2 * meters.gradients)
    assert not sample.gradients.flags.writeable


def test_gradient_queries_are_partition_independent_and_handle_empty_positions():
    config = WorldgenConfig(seed=319)
    config = replace(
        config,
        geology=replace(
            config.geology, plates=replace(config.geology.plates, plate_count=8)
        ),
    )
    field = generate_world_field(config)
    points = np.random.default_rng(414).uniform(-0.9, 0.9, (1031, 3))
    whole = field.elevation.sample_with_gradient(points)
    first = field.elevation.sample_with_gradient(points[:497])
    last = field.elevation.sample_with_gradient(points[497:])
    np.testing.assert_array_equal(
        whole.values, np.concatenate((first.values, last.values))
    )
    np.testing.assert_array_equal(
        whole.gradients, np.concatenate((first.gradients, last.gradients))
    )
    empty = field.elevation.sample_with_gradient(np.empty((0, 3)))
    assert empty.values.shape == (0,)
    assert empty.gradients.shape == (0, 3)


def test_world_region_vectors_and_pair_normals_round_trip_without_region_inputs():
    field = generate_world_field(WorldgenConfig(seed=2026))
    points = np.random.default_rng(441).uniform(-0.9, 0.9, (64, 3))
    transformed = field.warp.sample_with_jacobian(points)
    source = field.geology.motion.vectors.sample(transformed.values)
    world = field.sample_boundary_vectors(points)
    matrices = transformed.jacobians[world.query_indices]
    np.testing.assert_array_equal(world.region_pairs, source.region_pairs)
    np.testing.assert_allclose(
        pushforward_vectors(world.vectors, matrices[:, None]),
        source.vectors,
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        pushforward_normals(world.normals, matrices),
        source.normals,
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        pushforward_vectors(
            field.region_velocity.sample(points), transformed.jacobians
        ),
        field.geology.rotations.sample(transformed.values),
        rtol=1e-12,
        atol=1e-12,
    )
    empty = field.sample_boundary_vectors(np.empty((0, 3)))
    assert empty.vectors.shape == (0, 2, 3)
    assert empty.normals.shape == (0, 3)
