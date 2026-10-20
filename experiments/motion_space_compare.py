"""Temporary comparison of world-space motion and warped source relief."""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.worldgen.elevation.profiles import (
    collision_profile,
    divergent_profile,
    shear_profile,
)
from src.worldgen.field.boundary import (
    BoundaryInfluenceConfig,
    VoronoiBoundaryField,
    build_voronoi_boundary_field,
)
from src.worldgen.field.falloff import compact_influence
from src.worldgen.field.noise import NoiseConfig
from src.worldgen.field.regions import WarpedVoronoiField, build_warped_voronoi_field
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField
from src.worldgen.geology.config import PlateMotionConfig
from src.worldgen.geology.motion import generate_plate_motion
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.geometry.rotation import rotational_velocity
from src.worldgen.geometry.voronoi import voronoi_boundary_distances


WORLD_SEEDS = (123, 2026, 31415)
CASE_IDS = ("world-rigid", "transported-motion", "warped-relief")
CASE_TITLES = {
    "world-rigid": "A · World-space rigid motion",
    "transported-motion": "B · Warped source motion",
    "warped-relief": "C · Warped source relief",
}
NOISE_CONFIG = NoiseConfig(
    octaves=3, base_frequency=1.2, lacunarity=2.0, persistence=0.5
)
WARP_CONFIG = ShearWarpConfig(iterations=4, amplitude=0.24, lacunarity=1.7, gain=0.65)
SEED_COUNT = 32
BOUNDARY_WIDTH = 0.12
SAMPLE_BLOCK_SIZE = 1024


@dataclass(frozen=True, slots=True)
class ComparisonWorld:
    """One shared partition, boundary geometry, and set of region rotations."""

    regions: WarpedVoronoiField
    boundary: VoronoiBoundaryField
    angular_velocity: np.ndarray
    source_normals: np.ndarray


@dataclass(frozen=True, slots=True)
class FieldSample:
    """Categorical ownership and scalar diagnostic fields at query points."""

    ownership: np.ndarray
    opening: np.ndarray
    sliding: np.ndarray
    elevation: np.ndarray


def build_world(seed: int) -> ComparisonWorld:
    """Build one deterministic comparison world from isolated random streams."""
    streams = np.random.SeedSequence(seed).spawn(3)
    regions = build_warped_voronoi_field(
        SEED_COUNT,
        rng=np.random.default_rng(streams[0]),
        noise_seed=seed + 3000,
        noise_config=NOISE_CONFIG,
        warp_config=WARP_CONFIG,
    )
    angular_velocity = generate_plate_motion(
        regions.voronoi.seeds,
        PlateMotionConfig(),
        rng=np.random.default_rng(streams[2]),
    )
    boundary = build_voronoi_boundary_field(
        regions, BoundaryInfluenceConfig(width=BOUNDARY_WIDTH)
    )
    source_normals = np.stack([face.normal for face in boundary.geometry.faces])
    source_normals.setflags(write=False)
    return ComparisonWorld(
        regions=regions,
        boundary=boundary,
        angular_velocity=angular_velocity,
        source_normals=source_normals,
    )


def sample_warp_jacobian(
    warp: ShearWarpField,
    positions: np.ndarray,
    *,
    step: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Sample the warp and propagate a finite-difference Jacobian per shear."""
    source_points = np.array(positions, dtype=np.float64, copy=True)
    jacobians = np.broadcast_to(np.eye(3), (len(source_points), 3, 3)).copy()
    if (
        len(source_points) == 0
        or warp.config.iterations == 0
        or warp.config.amplitude == 0.0
    ):
        return source_points, jacobians

    for iteration in range(warp.config.iterations):
        scale = warp.config.amplitude * warp.config.gain**iteration
        frequency_multiplier = warp.config.lacunarity**iteration
        for axis in range(3):
            other_axes = tuple(index for index in range(3) if index != axis)
            plane = source_points[:, other_axes]
            gradient = np.empty((len(source_points), 2), dtype=np.float64)
            for plane_axis in range(2):
                plus = plane.copy()
                minus = plane.copy()
                plus[:, plane_axis] += step
                minus[:, plane_axis] -= step
                gradient[:, plane_axis] = (
                    warp.shear(plus, iteration, axis, frequency_multiplier)
                    - warp.shear(minus, iteration, axis, frequency_multiplier)
                ) / (2.0 * step)

            jacobians[:, axis, :] += scale * (
                gradient[:, 0, None] * jacobians[:, other_axes[0], :]
                + gradient[:, 1, None] * jacobians[:, other_axes[1], :]
            )
            offsets = warp.shear(plane, iteration, axis, frequency_multiplier)
            source_points[:, axis] += scale * offsets

    return source_points, jacobians


def evaluate_pair_motion(
    world_points: np.ndarray,
    source_points: np.ndarray,
    jacobians: np.ndarray,
    region_pairs: np.ndarray,
    source_normals: np.ndarray,
    angular_velocity: np.ndarray,
    *,
    case_id: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Return signed opening and shear magnitude for paired active faces."""
    interaction_count = len(region_pairs)
    if interaction_count == 0:
        return np.empty(0, dtype=np.float64), np.empty(0, dtype=np.float64)

    first_ids = region_pairs[:, 0]
    second_ids = region_pairs[:, 1]
    if case_id == "world-rigid":
        velocity_a = rotational_velocity(world_points, angular_velocity[first_ids])
        velocity_b = rotational_velocity(world_points, angular_velocity[second_ids])
        normals = np.einsum("nij,ni->nj", jacobians, source_normals)
        normals /= np.linalg.norm(normals, axis=1)[:, None]
    elif case_id == "transported-motion":
        source_velocity_a = rotational_velocity(
            source_points, angular_velocity[first_ids]
        )
        source_velocity_b = rotational_velocity(
            source_points, angular_velocity[second_ids]
        )
        source_velocities = np.stack((source_velocity_a, source_velocity_b), axis=1)
        world_velocities = np.linalg.solve(
            jacobians, source_velocities.swapaxes(1, 2)
        ).swapaxes(1, 2)
        velocity_a = world_velocities[:, 0, :]
        velocity_b = world_velocities[:, 1, :]
        normals = np.einsum("nij,ni->nj", jacobians, source_normals)
        normals /= np.linalg.norm(normals, axis=1)[:, None]
    elif case_id == "warped-relief":
        velocity_a = rotational_velocity(source_points, angular_velocity[first_ids])
        velocity_b = rotational_velocity(source_points, angular_velocity[second_ids])
        normals = source_normals
    else:
        raise ValueError(f"Unknown motion-space case: {case_id}")

    relative_velocity = velocity_b - velocity_a
    opening = np.einsum("ij,ij->i", relative_velocity, normals)
    sliding = np.linalg.norm(relative_velocity - opening[:, None] * normals, axis=1)
    return opening, sliding


def evaluate_relief(
    distances: np.ndarray,
    opening: np.ndarray,
    sliding: np.ndarray,
    *,
    width: float = BOUNDARY_WIDTH,
) -> np.ndarray:
    """Apply one shared dimensionless collision/rift/shear relief recipe."""
    if len(distances) == 0:
        return np.empty(0, dtype=np.float64)

    broad = np.empty(len(distances), dtype=np.float64)
    crest = np.empty(len(distances), dtype=np.float64)
    for index, distance in enumerate(distances):
        broad[index], crest[index] = collision_profile(float(distance), width, 0.2)
    divergent = np.fromiter(
        (
            divergent_profile(float(distance), width, continental=True)
            for distance in distances
        ),
        dtype=np.float64,
        count=len(distances),
    )
    shear = np.fromiter(
        (shear_profile(float(distance), width) for distance in distances),
        dtype=np.float64,
        count=len(distances),
    )
    collision = np.maximum(-opening, 0.0) * (0.65 * broad + 0.35 * crest)
    rift = np.maximum(opening, 0.0) * divergent
    return collision + rift + 0.15 * sliding * shear


def sample_comparison(
    world: ComparisonWorld,
    positions: np.ndarray,
    *,
    step: float = 0.001,
) -> dict[str, FieldSample]:
    """Sample all three interpretations at the same Cartesian positions."""
    query_points = np.asarray(positions, dtype=np.float64)
    count = len(query_points)
    ownership = np.empty(count, dtype=np.int64)
    output = {
        case_id: {
            "opening": np.zeros(count, dtype=np.float64),
            "sliding": np.zeros(count, dtype=np.float64),
            "elevation": np.zeros(count, dtype=np.float64),
        }
        for case_id in CASE_IDS
    }

    for start in range(0, count, SAMPLE_BLOCK_SIZE):
        stop = min(start + SAMPLE_BLOCK_SIZE, count)
        block = query_points[start:stop]
        source_points, jacobians = sample_warp_jacobian(
            world.regions.warp, block, step=step
        )
        ownership[start:stop] = world.regions.voronoi.sample(
            source_points
        ).owner_seed_id
        distances = voronoi_boundary_distances(source_points, world.boundary.geometry)
        influence = compact_influence(distances, width=BOUNDARY_WIDTH)
        query_indices, face_indices = np.nonzero(influence > 0.0)
        if len(query_indices) == 0:
            continue

        pairs = world.boundary.geometry.region_pairs[face_indices]
        pair_normals = world.source_normals[face_indices]
        pair_distances = distances[query_indices, face_indices]
        pair_influence = influence[query_indices, face_indices]
        pair_world_points = block[query_indices]
        pair_source_points = source_points[query_indices]
        pair_jacobians = jacobians[query_indices]

        for case_id in CASE_IDS:
            opening, sliding = evaluate_pair_motion(
                pair_world_points,
                pair_source_points,
                pair_jacobians,
                pairs,
                pair_normals,
                world.angular_velocity,
                case_id=case_id,
            )
            relief = evaluate_relief(pair_distances, opening, sliding)
            fields = output[case_id]
            block_count = stop - start
            fields["opening"][start:stop] = np.bincount(
                query_indices, weights=pair_influence * opening, minlength=block_count
            )
            fields["sliding"][start:stop] = np.bincount(
                query_indices, weights=pair_influence * sliding, minlength=block_count
            )
            fields["elevation"][start:stop] = np.bincount(
                query_indices, weights=relief, minlength=block_count
            )

    return {case_id: FieldSample(ownership, **output[case_id]) for case_id in CASE_IDS}


def _assert_empty_interactions() -> None:
    empty_points = np.empty((0, 3), dtype=np.float64)
    empty_pairs = np.empty((0, 2), dtype=np.int64)
    empty_normals = np.empty((0, 3), dtype=np.float64)
    empty_jacobians = np.empty((0, 3, 3), dtype=np.float64)
    empty_world = ShearWarpField(ShearWarpConfig(iterations=0), lambda *_: None)
    source, jacobians = sample_warp_jacobian(empty_world, empty_points, step=0.001)
    assert source.shape == (0, 3)
    assert jacobians.shape == (0, 3, 3)
    for case_id in CASE_IDS:
        opening, sliding = evaluate_pair_motion(
            empty_points,
            empty_points,
            empty_jacobians,
            empty_pairs,
            empty_normals,
            np.empty((0, 3), dtype=np.float64),
            case_id=case_id,
        )
        assert opening.shape == (0,)
        assert sliding.shape == (0,)
    assert evaluate_relief(np.empty(0), np.empty(0), np.empty(0)).shape == (0,)


def _check_identity_warps() -> None:
    points = np.array([[-0.4, 0.3, 0.1], [0.2, -0.5, 0.8]])
    pairs = np.array([[0, 1], [1, 2]], dtype=np.int64)
    normals = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    angular_velocity = np.array([[0.1, 0.2, 0.3], [-0.3, 0.1, 0.2], [0.2, -0.4, 0.1]])
    distances = np.array([0.0, 0.04])
    expected_opening = None
    expected_sliding = None
    expected_relief = None
    for config in (
        ShearWarpConfig(iterations=0),
        ShearWarpConfig(iterations=4, amplitude=0.0),
    ):
        warp = ShearWarpField(config, lambda *_: np.zeros(2))
        source, jacobians = sample_warp_jacobian(warp, points, step=0.001)
        np.testing.assert_array_equal(source, points)
        np.testing.assert_array_equal(jacobians, np.broadcast_to(np.eye(3), (2, 3, 3)))
        case_results = {
            case_id: evaluate_pair_motion(
                points,
                source,
                jacobians,
                pairs,
                normals,
                angular_velocity,
                case_id=case_id,
            )
            for case_id in CASE_IDS
        }
        for opening, sliding in case_results.values():
            if expected_opening is None:
                expected_opening = opening
                expected_sliding = sliding
            else:
                np.testing.assert_allclose(
                    opening, expected_opening, atol=1e-12, rtol=0.0
                )
                np.testing.assert_allclose(
                    sliding, expected_sliding, atol=1e-12, rtol=0.0
                )
        relief = evaluate_relief(distances, expected_opening, expected_sliding)
        if expected_relief is None:
            expected_relief = relief
        else:
            np.testing.assert_allclose(relief, expected_relief, atol=1e-12, rtol=0.0)
    _assert_empty_interactions()


def _check_affine_shear() -> tuple[ShearWarpField, np.ndarray, np.ndarray]:
    def affine_shear(
        plane: np.ndarray, iteration: int, axis: int, frequency_multiplier: float
    ) -> np.ndarray:
        if axis == 0:
            return plane[:, 0]
        return np.zeros(len(plane), dtype=np.float64)

    warp = ShearWarpField(
        ShearWarpConfig(iterations=1, amplitude=1.0, lacunarity=1.0, gain=1.0),
        affine_shear,
    )
    points = np.array([[-1.0, 1.0, 0.0], [0.0, 1.0, 0.0]])
    source, jacobians = sample_warp_jacobian(warp, points, step=0.001)
    np.testing.assert_allclose(
        source, [[0.0, 1.0, 0.0], [1.0, 1.0, 0.0]], atol=1e-10, rtol=0.0
    )
    expected_jacobian = np.array([[1.0, 1.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    np.testing.assert_allclose(
        jacobians,
        np.broadcast_to(expected_jacobian, (2, 3, 3)),
        atol=1e-10,
        rtol=0.0,
    )
    source_normal = np.array([[1.0, 0.0, 0.0]])
    world_normal = jacobians[:1].transpose(0, 2, 1) @ source_normal[:, :, None]
    world_normal = world_normal[:, :, 0]
    world_normal /= np.linalg.norm(world_normal, axis=1)[:, None]
    np.testing.assert_allclose(
        world_normal[0], [1.0, 1.0, 0.0] / np.sqrt(2.0), atol=1e-10, rtol=0.0
    )
    source_tangent = np.array([0.0, 1.0, 0.0])
    world_tangent = np.linalg.solve(expected_jacobian, source_tangent)
    np.testing.assert_allclose(world_tangent, [-1.0, 1.0, 0.0], atol=1e-10, rtol=0.0)
    np.testing.assert_allclose(
        np.dot(world_normal[0], world_tangent), 0.0, atol=1e-10, rtol=0.0
    )
    return warp, points, jacobians


def _check_affine_motion_profiles(points: np.ndarray, jacobians: np.ndarray) -> None:
    source_points = np.array([[0.0, 1.0, 0.0], [1.0, 1.0, 0.0]])
    pairs = np.array([[0, 1], [0, 1]], dtype=np.int64)
    normals = np.array([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    angular_velocity = np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 2.0]])
    expected = {
        "world-rigid": (
            [-np.sqrt(2.0), -1.0 / np.sqrt(2.0)],
            [0.0, 1.0 / np.sqrt(2.0)],
        ),
        "transported-motion": (
            [-1.0 / np.sqrt(2.0), -1.0 / np.sqrt(2.0)],
            [1.0 / np.sqrt(2.0), 3.0 / np.sqrt(2.0)],
        ),
        "warped-relief": ([-1.0, -1.0], [0.0, 1.0]),
    }
    for case_id, (expected_opening, expected_sliding) in expected.items():
        opening, sliding = evaluate_pair_motion(
            points,
            source_points,
            jacobians,
            pairs,
            normals,
            angular_velocity,
            case_id=case_id,
        )
        np.testing.assert_allclose(opening, expected_opening, atol=1e-10, rtol=0.0)
        np.testing.assert_allclose(sliding, expected_sliding, atol=1e-10, rtol=0.0)

    distance = np.zeros(1, dtype=np.float64)
    relief_expected = {
        "world-rigid": np.sqrt(2.0),
        "transported-motion": 1.15 / np.sqrt(2.0),
        "warped-relief": 1.0,
    }
    for case_id, expected_height in relief_expected.items():
        opening, sliding = evaluate_pair_motion(
            points[:1],
            source_points[:1],
            jacobians[:1],
            pairs[:1],
            normals[:1],
            angular_velocity,
            case_id=case_id,
        )
        height = evaluate_relief(distance, opening, sliding)
        np.testing.assert_allclose(height, [expected_height], atol=1e-10, rtol=0.0)


def _check_equal_motion_and_real_warp() -> None:
    points = np.random.default_rng(812).uniform(-1.0, 1.0, (1307, 3))
    world = build_world(2026)
    source, jacobians = sample_warp_jacobian(world.regions.warp, points, step=0.001)
    np.testing.assert_array_equal(source, world.regions.warp.sample(points))
    assert np.isfinite(source).all()
    assert np.isfinite(jacobians).all()
    np.testing.assert_allclose(np.linalg.det(jacobians), 1.0, atol=1e-7, rtol=1e-7)
    transformed_normals = np.einsum("nij,fi->nfj", jacobians, world.source_normals)
    normal_lengths = np.linalg.norm(transformed_normals, axis=2)
    normalized_normals = transformed_normals / normal_lengths[:, :, None]
    assert np.all(normal_lengths > 0.0)
    np.testing.assert_allclose(
        np.linalg.norm(normalized_normals, axis=2),
        np.ones_like(normal_lengths),
        atol=1e-10,
        rtol=0.0,
    )

    equal_rotation = np.repeat([[0.2, -0.1, 0.3]], 2, axis=0)
    equal_pairs = np.array([[0, 1]] * len(points), dtype=np.int64)
    equal_normals = np.broadcast_to([1.0, 0.0, 0.0], (len(points), 3))
    for case_id in CASE_IDS:
        opening, sliding = evaluate_pair_motion(
            points,
            source,
            jacobians,
            equal_pairs,
            equal_normals,
            equal_rotation,
            case_id=case_id,
        )
        np.testing.assert_allclose(opening, 0.0, atol=1e-12, rtol=0.0)
        np.testing.assert_allclose(sliding, 0.0, atol=1e-12, rtol=0.0)
        np.testing.assert_allclose(
            evaluate_relief(np.zeros(len(points)), opening, sliding),
            np.zeros(len(points)),
            atol=0.0,
            rtol=0.0,
        )

    distances = voronoi_boundary_distances(source, world.boundary.geometry)
    influence = compact_influence(distances, width=BOUNDARY_WIDTH)
    np.testing.assert_allclose(
        influence,
        world.boundary.sample(points).influence,
        atol=1e-12,
        rtol=0.0,
    )
    active_query, active_face = np.nonzero(influence > 0.0)
    assert len(active_query) > 0
    assert np.any(np.bincount(active_query, minlength=len(points)) > 1)
    pairs = world.boundary.geometry.region_pairs[active_face]
    normals = world.source_normals[active_face]
    b_opening, _ = evaluate_pair_motion(
        points[active_query],
        source[active_query],
        jacobians[active_query],
        pairs,
        normals,
        world.angular_velocity,
        case_id="transported-motion",
    )
    c_opening, _ = evaluate_pair_motion(
        points[active_query],
        source[active_query],
        jacobians[active_query],
        pairs,
        normals,
        world.angular_velocity,
        case_id="warped-relief",
    )
    world_normal_lengths = np.linalg.norm(
        np.einsum("nij,ni->nj", jacobians[active_query], normals), axis=1
    )
    np.testing.assert_allclose(
        b_opening,
        c_opening / world_normal_lengths,
        atol=1e-10,
        rtol=1e-10,
    )

    full = sample_comparison(world, points)
    chunks = [
        sample_comparison(world, points[:500]),
        sample_comparison(world, points[500:]),
    ]
    permutation = np.random.default_rng(71).permutation(len(points))
    reordered = sample_comparison(world, points[permutation])
    singleton = sample_comparison(world, points[:1])
    for case_id in CASE_IDS:
        for field_name in ("ownership", "opening", "sliding", "elevation"):
            full_values = getattr(full[case_id], field_name)
            chunk_values = np.concatenate(
                [getattr(chunk[case_id], field_name) for chunk in chunks]
            )
            np.testing.assert_allclose(
                chunk_values, full_values, atol=1e-10, rtol=1e-10
            )
            np.testing.assert_allclose(
                getattr(reordered[case_id], field_name),
                full_values[permutation],
                atol=1e-10,
                rtol=1e-10,
            )
            np.testing.assert_allclose(
                getattr(singleton[case_id], field_name),
                full_values[:1],
                atol=1e-10,
                rtol=1e-10,
            )


def check_comparison() -> None:
    """Run deterministic analytic and real-warp checks for this experiment."""
    initial_rng_state = np.random.get_state()
    _check_identity_warps()
    _assert_empty_interactions()
    _, points, jacobians = _check_affine_shear()
    _check_affine_motion_profiles(points, jacobians)
    _check_equal_motion_and_real_warp()
    final_rng_state = np.random.get_state()
    assert initial_rng_state[0] == final_rng_state[0]
    np.testing.assert_array_equal(initial_rng_state[1], final_rng_state[1])
    assert initial_rng_state[2:] == final_rng_state[2:]


def _regular_xy_points(
    resolution: int, lower: float = -1.0, upper: float = 1.0
) -> np.ndarray:
    axis = np.linspace(lower, upper, resolution)
    x, y = np.meshgrid(axis, axis)
    return np.column_stack((x.ravel(), y.ravel(), np.zeros(x.size)))


def _sample_vector_arrows(
    world: ComparisonWorld,
    points: np.ndarray,
    *,
    case_id: str,
) -> dict[str, np.ndarray]:
    """Sample strongest-pair vectors for the diagnostic XY quiver panel."""
    if case_id == "warped-relief":
        source_points = np.array(points, dtype=np.float64, copy=True)
        jacobians = np.broadcast_to(np.eye(3), (len(points), 3, 3)).copy()
    else:
        source_points, jacobians = sample_warp_jacobian(
            world.regions.warp, points, step=0.001
        )

    owners = world.regions.voronoi.sample(source_points).owner_seed_id
    distances = voronoi_boundary_distances(source_points, world.boundary.geometry)
    influence = compact_influence(distances, width=BOUNDARY_WIDTH)
    strongest_face = np.argmax(influence, axis=1)
    strongest_value = influence[np.arange(len(points)), strongest_face]
    query_indices = np.flatnonzero(strongest_value > 0.0)
    face_indices = strongest_face[query_indices]
    pairs = world.boundary.geometry.region_pairs[face_indices]
    normals = world.source_normals[face_indices]
    active_source = source_points[query_indices]

    if case_id == "world-rigid":
        active_world = points[query_indices]
        active_jacobians = jacobians[query_indices]
        velocity_a = rotational_velocity(
            active_world, world.angular_velocity[pairs[:, 0]]
        )
        velocity_b = rotational_velocity(
            active_world, world.angular_velocity[pairs[:, 1]]
        )
        normals = np.einsum("nij,ni->nj", active_jacobians, normals)
        normals /= np.linalg.norm(normals, axis=1)[:, None]
        arrow_points = active_world
    elif case_id == "transported-motion":
        active_world = points[query_indices]
        active_jacobians = jacobians[query_indices]
        source_velocity_a = rotational_velocity(
            active_source, world.angular_velocity[pairs[:, 0]]
        )
        source_velocity_b = rotational_velocity(
            active_source, world.angular_velocity[pairs[:, 1]]
        )
        source_velocities = np.stack((source_velocity_a, source_velocity_b), axis=1)
        world_velocities = np.linalg.solve(
            active_jacobians, source_velocities.swapaxes(1, 2)
        ).swapaxes(1, 2)
        velocity_a = world_velocities[:, 0, :]
        velocity_b = world_velocities[:, 1, :]
        normals = np.einsum("nij,ni->nj", active_jacobians, normals)
        normals /= np.linalg.norm(normals, axis=1)[:, None]
        arrow_points = active_world
    elif case_id == "warped-relief":
        velocity_a = rotational_velocity(
            active_source, world.angular_velocity[pairs[:, 0]]
        )
        velocity_b = rotational_velocity(
            active_source, world.angular_velocity[pairs[:, 1]]
        )
        arrow_points = active_source
    else:
        raise ValueError(f"Unknown motion-space case: {case_id}")

    return {
        "points": arrow_points,
        "ownership": owners,
        "velocity_a": velocity_a,
        "velocity_b": velocity_b,
        "normal": normals,
    }


def _palette() -> np.ndarray:
    return np.rint(
        plt.get_cmap("gist_ncar")(np.linspace(0.05, 0.95, SEED_COUNT))[:, :3] * 255
    ).astype(np.uint8)


def _draw_owner_outlines(axis, ownership: np.ndarray, resolution: int) -> None:
    from matplotlib.collections import LineCollection

    coordinates = np.linspace(-1.0, 1.0, resolution)
    owners = ownership.reshape((resolution, resolution))
    step = coordinates[1] - coordinates[0]
    row, column = np.nonzero(owners[:, :-1] != owners[:, 1:])
    x = 0.5 * (coordinates[column] + coordinates[column + 1])
    y = coordinates[row]
    vertical = np.stack(
        (
            np.column_stack((x, y - 0.5 * step)),
            np.column_stack((x, y + 0.5 * step)),
        ),
        axis=1,
    )
    row, column = np.nonzero(owners[:-1, :] != owners[1:, :])
    y = 0.5 * (coordinates[row] + coordinates[row + 1])
    x = coordinates[column]
    horizontal = np.stack(
        (
            np.column_stack((x - 0.5 * step, y)),
            np.column_stack((x + 0.5 * step, y)),
        ),
        axis=1,
    )
    segments = np.concatenate((vertical, horizontal), axis=0)
    axis.add_collection(
        LineCollection(segments, colors="black", linewidths=0.45, alpha=0.85)
    )


def _render_ownership(
    ownership: np.ndarray,
    resolution: int,
    output: Path,
    palette: np.ndarray,
    *,
    title: str,
) -> None:
    fig, axis = plt.subplots(figsize=(10, 9), layout="constrained")
    axis.imshow(
        palette[ownership].reshape((resolution, resolution, 3)),
        origin="lower",
        extent=(-1.0, 1.0, -1.0, 1.0),
        interpolation="nearest",
    )
    _draw_owner_outlines(axis, ownership, resolution)
    axis.set(title=title, xlabel="x", ylabel="y", aspect="equal")
    fig.savefig(output, dpi=100)
    plt.close(fig)


def _render_vectors(
    arrows: dict[str, np.ndarray],
    resolution: int,
    output: Path,
    palette: np.ndarray,
    *,
    case_id: str,
    vector_scale: float,
) -> None:
    from matplotlib.lines import Line2D

    owners = arrows["ownership"]
    fig, axis = plt.subplots(figsize=(10, 9), layout="constrained")
    axis.imshow(
        palette[owners].reshape((resolution, resolution, 3)),
        origin="lower",
        extent=(-1.0, 1.0, -1.0, 1.0),
        interpolation="nearest",
        alpha=0.76,
    )
    _draw_owner_outlines(axis, owners, resolution)
    positions = arrows["points"]
    velocity_a = arrows["velocity_a"]
    velocity_b = arrows["velocity_b"]
    normals = arrows["normal"]
    axis.quiver(
        positions[:, 0],
        positions[:, 1],
        velocity_a[:, 0],
        velocity_a[:, 1],
        angles="xy",
        scale_units="xy",
        scale=vector_scale,
        color="#e4572e",
        width=0.003,
        headwidth=3.5,
        zorder=3,
    )
    axis.quiver(
        positions[:, 0],
        positions[:, 1],
        velocity_b[:, 0],
        velocity_b[:, 1],
        angles="xy",
        scale_units="xy",
        scale=vector_scale,
        color="#1768ac",
        width=0.003,
        headwidth=3.5,
        zorder=3,
    )
    axis.quiver(
        positions[:, 0],
        positions[:, 1],
        0.04 * normals[:, 0],
        0.04 * normals[:, 1],
        angles="xy",
        scale_units="xy",
        scale=1.0,
        color="black",
        width=0.002,
        headwidth=3.0,
        zorder=4,
    )
    legend = [
        Line2D([0], [0], color="#e4572e", lw=2, label="Region A velocity"),
        Line2D([0], [0], color="#1768ac", lw=2, label="Region B velocity"),
        Line2D([0], [0], color="black", lw=2, label="Oriented normal (0.04)"),
    ]
    axis.legend(handles=legend, loc="lower left", framealpha=0.9, fontsize=9)
    caption = "x\nXY components only; calculations use all XYZ components."
    if case_id == "warped-relief":
        caption += (
            "\nSource-space reference; not a world-space vector field; "
            "not the same query sheet as A/B."
        )
    axis.set(
        title=CASE_TITLES[case_id],
        xlabel=caption,
        ylabel="y",
        xlim=(-1.0, 1.0),
        ylim=(-1.0, 1.0),
        aspect="equal",
    )
    axis.xaxis.label.set_size(9)
    fig.savefig(output, dpi=100)
    plt.close(fig)


def _render_scalar(
    values: np.ndarray,
    ownership: np.ndarray,
    resolution: int,
    output: Path,
    *,
    case_id: str,
    field_name: str,
    limits: tuple[float, float],
) -> None:
    colormaps = {
        "opening": ("RdBu_r", "Opening (signed; compression < 0)"),
        "sliding": ("magma", "Sliding magnitude"),
        "elevation": ("BrBG_r", "Dimensionless diagnostic relief"),
    }
    cmap, label = colormaps[field_name]
    fig, axis = plt.subplots(figsize=(10, 9), layout="constrained")
    image = axis.imshow(
        values.reshape((resolution, resolution)),
        origin="lower",
        extent=(-1.0, 1.0, -1.0, 1.0),
        cmap=cmap,
        vmin=limits[0],
        vmax=limits[1],
        interpolation="nearest",
    )
    _draw_owner_outlines(axis, ownership, resolution)
    axis.set(
        title=f"{CASE_TITLES[case_id]} · {label}",
        xlabel="x",
        ylabel="y",
        aspect="equal",
    )
    colorbar = fig.colorbar(image, ax=axis, orientation="horizontal", pad=0.08)
    colorbar.set_label(label)
    fig.savefig(output, dpi=100)
    plt.close(fig)


def _render_globe(
    points: np.ndarray,
    faces: np.ndarray,
    elevation: np.ndarray,
    output: Path,
    *,
    limits: tuple[float, float],
    radial_factor: float,
) -> None:
    import pyvista as pv

    displaced = points * (1.0 + radial_factor * elevation[:, None])
    cells = np.column_stack((np.full(len(faces), 3, dtype=np.int64), faces)).ravel()
    surface = pv.PolyData(displaced, cells)
    surface.point_data["elevation"] = elevation
    plotter = pv.Plotter(off_screen=True, shape=(1, 2), window_size=(1400, 700))
    directions = ((1.6, -2.4, 1.2), (-1.8, 1.6, -0.6))
    try:
        for column, direction in enumerate(directions):
            plotter.subplot(0, column)
            plotter.set_background("#f4f6f8")
            plotter.add_mesh(
                surface,
                scalars="elevation",
                cmap="BrBG_r",
                clim=limits,
                show_scalar_bar=column == 1,
                scalar_bar_args={
                    "title": "Elevation (dimensionless)",
                    "vertical": False,
                    "position_x": 0.16,
                    "position_y": 0.06,
                    "width": 0.68,
                    "height": 0.08,
                    "n_labels": 5,
                    "fmt": "%.3f",
                    "title_font_size": 14,
                    "label_font_size": 11,
                    "color": "#18212b",
                },
                show_edges=False,
                ambient=0.65,
                diffuse=0.35,
                specular=0.0,
                smooth_shading=True,
            )
            plotter.camera_position = (direction, (0, 0, 0), (0, 0, 1))
            plotter.enable_parallel_projection()
            plotter.camera.parallel_scale = 1.1
            plotter.add_text(
                f"View {'AB'[column]}",
                position="upper_left",
                font_size=13,
                color="#18212b",
            )
        plotter.screenshot(str(output))
    finally:
        plotter.close()


def _field_metrics(values: np.ndarray) -> dict[str, float]:
    return {
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "rms": float(np.sqrt(np.mean(values**2))),
    }


def _difference_metrics(first: np.ndarray, second: np.ndarray) -> dict[str, float]:
    difference = first - second
    return {
        "rms_difference": float(np.sqrt(np.mean(difference**2))),
        "max_abs_difference": float(np.max(np.abs(difference))),
    }


def _pairwise_comparisons(
    samples: dict[str, FieldSample],
) -> list[dict[str, object]]:
    comparisons = []
    for first_index, first_id in enumerate(CASE_IDS):
        for second_id in CASE_IDS[first_index + 1 :]:
            record: dict[str, object] = {
                "cases": [first_id, second_id],
                "slice": {},
                "sphere": {},
            }
            for surface_name, surface_samples in samples.items():
                values = {}
                for field_name in ("opening", "sliding", "elevation"):
                    values[field_name] = _difference_metrics(
                        getattr(surface_samples[first_id], field_name),
                        getattr(surface_samples[second_id], field_name),
                    )
                record[surface_name] = values
            comparisons.append(record)
    return comparisons


def _derivative_sensitivity(
    world: ComparisonWorld,
) -> dict[str, object]:
    probe = np.random.default_rng(812).uniform(-1.0, 1.0, (1307, 3))
    primary = sample_comparison(world, probe, step=0.001)
    alternatives = {
        step: sample_comparison(world, probe, step=step) for step in (0.002, 0.0005)
    }
    measurements: dict[str, object] = {}
    warnings: list[str] = []
    for case_id in CASE_IDS:
        measurements[case_id] = {}
        for field_name in ("opening", "sliding", "elevation"):
            primary_values = getattr(primary[case_id], field_name)
            measurements[case_id][field_name] = {}
            for step, sample in alternatives.items():
                alternate_values = getattr(sample[case_id], field_name)
                difference = alternate_values - primary_values
                numerator = np.linalg.norm(difference)
                denominator = np.linalg.norm(primary_values)
                if denominator == 0.0:
                    relative_difference = 0.0 if numerator == 0.0 else None
                    if numerator != 0.0:
                        warnings.append(
                            f"{case_id} {field_name} has zero primary norm and "
                            f"nonzero difference at step {step:g}."
                        )
                else:
                    relative_difference = float(numerator / denominator)
                metric = {
                    "rms_difference": float(np.sqrt(np.mean(difference**2))),
                    "max_abs_difference": float(np.max(np.abs(difference))),
                    "relative_rms_difference": relative_difference,
                }
                measurements[case_id][field_name][str(step)] = metric
                if (
                    case_id in ("world-rigid", "transported-motion")
                    and relative_difference is not None
                    and relative_difference > 0.05
                ):
                    warnings.append(
                        f"{case_id} {field_name} relative RMS difference "
                        f"{relative_difference:.6g} exceeds 0.05 at step {step:g}."
                    )

    for step, sample in alternatives.items():
        for field_name in ("opening", "sliding", "elevation"):
            np.testing.assert_array_equal(
                getattr(sample["warped-relief"], field_name),
                getattr(primary["warped-relief"], field_name),
            )
    return {
        "probe_count": len(probe),
        "steps": [0.001, 0.002, 0.0005],
        "metrics": measurements,
        "warning": " ".join(warnings) if warnings else None,
    }


def _save_world_arrays(
    output: Path,
    world: ComparisonWorld,
    slice_points: np.ndarray,
    sphere_points: np.ndarray,
    slice_samples: dict[str, FieldSample],
    sphere_samples: dict[str, FieldSample],
    *,
    seed: int,
) -> str:
    filename = f"motion-{seed}-fields.npz"
    arrays: dict[str, np.ndarray] = {
        "seeds": world.regions.voronoi.seeds,
        "angular_velocity": world.angular_velocity,
        "slice_points": slice_points,
        "sphere_points": sphere_points,
        "slice_ownership": slice_samples[CASE_IDS[0]].ownership,
        "sphere_ownership": sphere_samples[CASE_IDS[0]].ownership,
    }
    for case_id in CASE_IDS:
        for surface_name, samples in (
            ("slice", slice_samples),
            ("sphere", sphere_samples),
        ):
            for field_name in ("opening", "sliding", "elevation"):
                arrays[f"{case_id}_{surface_name}_{field_name}"] = getattr(
                    samples[case_id], field_name
                )
    np.savez(output / filename, **arrays)
    return filename


def _common_limits(
    world_data: list[dict[str, object]],
) -> dict[str, tuple[float, float]]:
    maxima = {"opening": 0.0, "sliding": 0.0, "elevation": 0.0}
    for entry in world_data:
        for samples in (entry["slice_samples"], entry["sphere_samples"]):
            for case_id in CASE_IDS:
                for field_name in maxima:
                    values = getattr(samples[case_id], field_name)
                    maxima[field_name] = max(
                        maxima[field_name], float(np.max(np.abs(values)))
                    )
    return {
        "opening": (-maxima["opening"], maxima["opening"]),
        "sliding": (0.0, maxima["sliding"]),
        "elevation": (-maxima["elevation"], maxima["elevation"]),
    }


def _run_experiment(output: Path, frequency: int, slice_resolution: int) -> None:
    output.mkdir(parents=True, exist_ok=True)
    vertices, faces = generate_icosphere(frequency)
    slice_points = _regular_xy_points(slice_resolution)
    vector_points = _regular_xy_points(20, -0.95, 0.95)
    world_data: list[dict[str, object]] = []
    calculation_started = perf_counter()
    print(
        f"Starting matched sampling: {len(slice_points):,} slice points, "
        f"{len(vertices):,} sphere points, {len(WORLD_SEEDS)} worlds.",
        flush=True,
    )

    for seed in WORLD_SEEDS:
        world_started = perf_counter()
        world = build_world(seed)
        print(
            f"[{seed}] Built shared 32-seed partition and boundary geometry.",
            flush=True,
        )
        slice_started = perf_counter()
        slice_samples = sample_comparison(world, slice_points, step=0.001)
        print(
            f"[{seed}] Sampled slice fields in {perf_counter() - slice_started:.2f}s.",
            flush=True,
        )
        sphere_started = perf_counter()
        sphere_samples = sample_comparison(world, vertices, step=0.001)
        print(
            f"[{seed}] Sampled sphere fields in {perf_counter() - sphere_started:.2f}s.",
            flush=True,
        )
        sensitivity_started = perf_counter()
        derivative_sensitivity = _derivative_sensitivity(world)
        probe = np.random.default_rng(812).uniform(-1.0, 1.0, (1307, 3))
        probe_samples = sample_comparison(world, probe, step=0.001)
        print(
            f"[{seed}] Completed derivative sensitivity and repeatability probes "
            f"in {perf_counter() - sensitivity_started:.2f}s.",
            flush=True,
        )
        fields_file = _save_world_arrays(
            output,
            world,
            slice_points,
            vertices,
            slice_samples,
            sphere_samples,
            seed=seed,
        )
        world_data.append(
            {
                "seed": seed,
                "world": world,
                "slice_samples": slice_samples,
                "sphere_samples": sphere_samples,
                "probe_samples": probe_samples,
                "derivative_sensitivity": derivative_sensitivity,
                "fields_file": fields_file,
            }
        )
        if derivative_sensitivity["warning"]:
            print(
                f"[{seed}] Derivative-sensitive; appearance is exploratory. "
                f"{derivative_sensitivity['warning']}",
                flush=True,
            )
        else:
            print(f"[{seed}] No step-sensitivity threshold crossed.", flush=True)
        print(
            f"[{seed}] Calculation phase complete in "
            f"{perf_counter() - world_started:.2f}s.",
            flush=True,
        )

    color_limits = _common_limits(world_data)
    arrow_data: dict[tuple[int, str], dict[str, np.ndarray]] = {}
    vector_maximum = 0.0
    for entry in world_data:
        for case_id in CASE_IDS:
            arrows = _sample_vector_arrows(
                entry["world"], vector_points, case_id=case_id
            )
            arrow_data[(entry["seed"], case_id)] = arrows
            if len(arrows["points"]):
                vector_maximum = max(
                    vector_maximum,
                    float(np.max(np.linalg.norm(arrows["velocity_a"], axis=1))),
                    float(np.max(np.linalg.norm(arrows["velocity_b"], axis=1))),
                )
    calculation_seconds = perf_counter() - calculation_started
    vector_scale = vector_maximum / 0.08
    elevation_maximum = color_limits["elevation"][1]
    radial_factor = 0.06 / elevation_maximum
    print(
        f"Common scales: opening={color_limits['opening']}, "
        f"sliding={color_limits['sliding']}, elevation={color_limits['elevation']}, "
        f"velocity quiver scale={vector_scale:.8g}, globe radial factor={radial_factor:.8g}.",
        flush=True,
    )

    render_started = perf_counter()
    palette = _palette()
    manifest_worlds: list[dict[str, object]] = []
    globe_error: str | None = None
    for entry in world_data:
        seed = entry["seed"]
        world = entry["world"]
        slice_samples = entry["slice_samples"]
        sphere_samples = entry["sphere_samples"]
        ownership_image = f"motion-{seed}-ownership.png"
        _render_ownership(
            slice_samples[CASE_IDS[0]].ownership,
            slice_resolution,
            output / ownership_image,
            palette,
            title=f"Warped Voronoi ownership · seed {seed}",
        )
        case_records = []
        for case_id in CASE_IDS:
            image_paths = {
                "vectors": f"motion-{seed}-{case_id}-vectors.png",
                "opening": f"motion-{seed}-{case_id}-opening.png",
                "sliding": f"motion-{seed}-{case_id}-sliding.png",
                "elevation": f"motion-{seed}-{case_id}-elevation.png",
                "globe": f"motion-{seed}-{case_id}-globe.png",
            }
            arrows = arrow_data[(seed, case_id)]
            _render_vectors(
                arrows,
                20,
                output / image_paths["vectors"],
                palette,
                case_id=case_id,
                vector_scale=vector_scale,
            )
            for field_name, limits in color_limits.items():
                _render_scalar(
                    getattr(slice_samples[case_id], field_name),
                    slice_samples[case_id].ownership,
                    slice_resolution,
                    output / image_paths[field_name],
                    case_id=case_id,
                    field_name=field_name,
                    limits=limits,
                )
            if globe_error is None:
                try:
                    _render_globe(
                        vertices,
                        faces,
                        sphere_samples[case_id].elevation,
                        output / image_paths["globe"],
                        limits=color_limits["elevation"],
                        radial_factor=radial_factor,
                    )
                except Exception as error:
                    globe_error = f"{type(error).__name__}: {error}"
                    print(f"Globe rendering failed: {globe_error}", flush=True)
            scalar_metrics = {}
            for surface_name, samples in (
                ("slice", slice_samples),
                ("sphere", sphere_samples),
            ):
                scalar_metrics[surface_name] = {
                    field_name: _field_metrics(getattr(samples[case_id], field_name))
                    for field_name in ("opening", "sliding", "elevation")
                }
            case_records.append(
                {
                    "id": case_id,
                    "title": CASE_TITLES[case_id],
                    "vector_frame": (
                        "source-reference" if case_id == "warped-relief" else "world"
                    ),
                    "images": image_paths,
                    "metrics": scalar_metrics,
                }
            )
        manifest_worlds.append(
            {
                "seed": seed,
                "ownership_image": ownership_image,
                "fields_file": entry["fields_file"],
                "cases": case_records,
                "comparisons": _pairwise_comparisons(
                    {
                        "slice": slice_samples,
                        "sphere": sphere_samples,
                    }
                ),
                "derivative_sensitivity": entry["derivative_sensitivity"],
            }
        )
        for surface_name, samples in (
            ("slice", slice_samples),
            ("sphere", sphere_samples),
        ):
            for case_id in CASE_IDS:
                for field_name in ("opening", "sliding", "elevation"):
                    metric = _field_metrics(getattr(samples[case_id], field_name))
                    print(
                        f"[{seed} {surface_name} {case_id} {field_name}] "
                        f"min={metric['min']:.7g} max={metric['max']:.7g} "
                        f"rms={metric['rms']:.7g}",
                        flush=True,
                    )
        for comparison in manifest_worlds[-1]["comparisons"]:
            for surface_name in ("slice", "sphere"):
                print(
                    f"[{seed} {surface_name} {comparison['cases'][0]} vs "
                    f"{comparison['cases'][1]}] {comparison[surface_name]}",
                    flush=True,
                )
        print(
            f"[{seed}] Rendered ownership, slice/vector panels, and globe when available.",
            flush=True,
        )

    if globe_error is not None:
        for seed in WORLD_SEEDS:
            for case_id in CASE_IDS:
                (output / f"motion-{seed}-{case_id}-globe.png").unlink(missing_ok=True)
        for world_record in manifest_worlds:
            for case_record in world_record["cases"]:
                case_record["images"]["globe"] = None

    render_seconds = perf_counter() - render_started
    settings = {
        "seeds": list(WORLD_SEEDS),
        "seed_count": SEED_COUNT,
        "noise": {
            "octaves": NOISE_CONFIG.octaves,
            "base_frequency": NOISE_CONFIG.base_frequency,
            "lacunarity": NOISE_CONFIG.lacunarity,
            "persistence": NOISE_CONFIG.persistence,
        },
        "shear_warp": {
            "iterations": WARP_CONFIG.iterations,
            "amplitude": WARP_CONFIG.amplitude,
            "lacunarity": WARP_CONFIG.lacunarity,
            "gain": WARP_CONFIG.gain,
        },
        "boundary_support_width_source": BOUNDARY_WIDTH,
        "profile_recipe": {
            "crust_assumption": "uniform continental",
            "collision_crest_width_fraction": 0.2,
            "collision_broad_weight": 0.65,
            "collision_crest_weight": 0.35,
            "shear_relief_weight": 0.15,
            "relief_units": "dimensionless diagnostic values",
        },
        "slice_resolution": slice_resolution,
        "frequency": frequency,
        "cell_count": len(vertices),
        "derivative_primary_step": 0.001,
        "derivative_probe_steps": [0.002, 0.0005],
        "derivative_probe_count": 1307,
        "scalar_color_limits": {
            name: list(limits) for name, limits in color_limits.items()
        },
        "velocity_max_full_3d_magnitude": vector_maximum,
        "velocity_quiver_scale": vector_scale,
        "max_velocity_arrow_plot_length": 0.08,
        "normal_arrow_plot_length": 0.04,
        "globe_radial_factor": radial_factor,
        "interaction_space": "cartesian-3d",
    }
    manifest = {
        "settings": settings,
        "worlds": manifest_worlds,
        "timings_seconds": {
            "calculation": calculation_seconds,
            "render": render_seconds,
        },
        "globe_render_error": globe_error,
    }
    with (output / "motion-space-results.json").open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2, allow_nan=False)
        file.write("\n")
    _publish_gallery(output)
    print(
        f"Shared calculation phase {calculation_seconds:.2f}s; shared render phase "
        f"{render_seconds:.2f}s. Wrote results to {output}.",
        flush=True,
    )


def _publish_gallery(output: Path) -> None:
    """Copy the comparison page and add its idempotent link to a local index."""
    template = Path(__file__).with_name("motion_space_compare.html")
    (output / "motion-space.html").write_text(
        template.read_text(encoding="utf-8"), encoding="utf-8"
    )
    index_path = output / "index.html"
    if not index_path.exists():
        return

    content = index_path.read_text(encoding="utf-8")
    preview_path = output / "motion-2026-warped-relief-globe.png"
    if preview_path.exists():
        preview = (
            '<a href="motion-space.html"><img '
            'src="motion-2026-warped-relief-globe.png" '
            'alt="Warped source relief on the unit-sphere observation surface, '
            'world seed 2026, two fixed views"></a>'
        )
    else:
        preview = (
            "<p>Globe preview unavailable; see the comparison manifest "
            "for the renderer error.</p>"
        )
    section = (
        "<section>\n"
        "<h1>Motion spaces: warp motion or warp relief?</h1>\n"
        "<p>Three matched worlds compare rigid world-space motion, transported "
        "source-space motion, and source-space relief carried through the warp.</p>\n"
        '<p><a href="motion-space.html"><strong>Open the motion-space '
        "comparison</strong></a></p>\n"
        f"{preview}\n"
        "<p>This is a temporary diagnostic; the production generator is "
        "unchanged. Earlier experiments remain below.</p>\n"
        "</section>"
    )
    heading_marker = "<h1>Motion spaces: warp motion or warp relief?</h1>"
    if heading_marker in content:
        heading_position = content.index(heading_marker)
        section_start = content.rfind("<section", 0, heading_position)
        section_end = content.index("</section>", heading_position) + len("</section>")
        content = content[:section_start] + section + content[section_end:]
    else:
        main_marker = "<body><main>"
        insertion = content.index(main_marker) + len(main_marker)
        content = content[:insertion] + "\n" + section + content[insertion:]
    index_path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("/tmp/domain-warp-voronoi-site")
    )
    parser.add_argument("--frequency", type=int, default=80)
    parser.add_argument("--slice-resolution", type=int, default=320)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    check_comparison()
    print("Motion-space analytic checks passed.", flush=True)
    if args.check:
        return
    _run_experiment(args.output, args.frequency, args.slice_resolution)


if __name__ == "__main__":
    main()
